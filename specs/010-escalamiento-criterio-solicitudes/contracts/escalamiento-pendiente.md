# Contrato: escalamiento pendiente (`src/agente_disputas/controles.py`)

Fundamento en [research.md](../research.md) R1 a R5; entidades en
[data-model.md](../data-model.md).

## Registro en las opciones (`Controles.hooks()`)

```text
"PreToolUse":       [sin cambios: consultar|iniciar_disputa|bloquear → antes_de_herramienta]
"PostToolUse":      [verificar_identidad → despues_de_verificar,           (sin cambios)
                     iniciar_disputa     → despues_de_disputar,            (nuevo)
                     escalar_a_analista  → despues_de_escalar]             (nuevo)
"Stop":             [matcher None → antes_de_terminar]                     (nuevo)
"UserPromptSubmit": [matcher None → al_recibir_mensaje]                    (nuevo)
```

Todos con `timeout=TIEMPO_MAXIMO_SEGUNDOS` y nombres completos `mcp__core-bancario__...`.

## Callbacks nuevos

| Callback | Entrada relevante | Efecto | Salida |
|---|---|---|---|
| `antes_de_herramienta` (cambio) | negación `REQUIERE_ANALISTA` de `TRX` | `pendientes[TRX] = "umbral"` | la misma negación del #9 |
| `despues_de_disputar` | `tool_input.transaccion_id`, `tool_response` | `ok: false` con `FUERA_DE_POLITICA` → `pendientes[TRX] = "fuera_de_politica"`; con `REQUIERE_ANALISTA` → `"umbral"`; otra cosa → nada | `{}` |
| `despues_de_escalar` | `tool_input.causa`, `tool_input.transacciones`, `tool_response` | `ok: true` → quita los pendientes cuyo id está en `lista_de_ids(transacciones)` y cuya causa es `causa.strip()`; otra cosa → nada | `{}` |
| `antes_de_terminar` | — | con pendientes y `cierres_impedidos < 2`: `cierres_impedidos += 1` | `{"decision": "block", "reason": <razón>}` |
| | | sin pendientes o tope alcanzado | `{}` |
| `al_recibir_mensaje` | — | `pendientes = {}`, `cierres_impedidos = 0` | `{}` |

- **Razón del `Stop`**: en español, nombra cada transacción pendiente con su causa y pide
  escalar con `escalar_a_analista` incluyendo cliente, transacciones, acciones realizadas y
  acción recomendada. Solo ids y causas: nada de montos ni datos de otros clientes.
- **Nunca lanzan**: una excepción en los `PostToolUse` o en `al_recibir_mensaje` no cambia el
  estado y devuelve `{}`; en `antes_de_terminar` devuelve `{}` (deja terminar; R4).

## Interfaz (`src/agente_disputas/cli.py`)

- `conversar(cliente, leer, escribir, controles=None)`: tras escribir la respuesta de un turno,
  si `controles` y `controles.estado.pendientes` no está vacío, escribe
  `AVISO_ESCALAMIENTO_PENDIENTE`.
- `_ejecutar(entorno)` crea los `Controles`, los pasa a `crear_opciones` y a `conversar`.

## Tests deterministas (sin API)

En `src/agente_disputas/test_controles.py`:

1. Negación por umbral de `TRX-002` → `pendientes == {"TRX-002": "umbral"}`; negaciones por
   identidad, titularidad o falla → sin pendientes.
2. `despues_de_disputar` con `FUERA_DE_POLITICA` (TRX-006) → pendiente `fuera_de_politica`;
   con `REQUIERE_ANALISTA` → `umbral`; con éxito, otro error o respuesta ilegible → nada.
3. `antes_de_terminar`: sin pendientes → `{}`; con pendiente → bloquea dos veces con razón que
   nombra `TRX-002` y "umbral"; la tercera → `{}` y el pendiente sigue.
4. `despues_de_escalar`: éxito con `["TRX-002"]` y causa `umbral` → limpia; con texto JSON
   `'["TRX-002"]'` → limpia; sin la transacción, con otra causa, con `ok: false` o ilegible →
   no limpia; con dos pendientes y una sola escalada → queda la otra.
5. `al_recibir_mensaje` → vacía pendientes y reinicia el tope.
6. **Mensaje de ejemplo** (FR-006): CLI-001 verificado; `TRX-002` negada por umbral; después
   `TRX-001` y el bloqueo de la 4821 se autorizan (`{}`); `antes_de_terminar` bloquea; tras
   escalar `TRX-002` con causa `umbral`, `antes_de_terminar` → `{}`.
7. Excepciones internas (entradas `None`, `tool_input` no dict) → `{}` sin cambiar el estado.

En `src/agente_disputas/test_configuracion.py`: los cuatro eventos registrados con sus
matchers exactos.

En `src/agente_disputas/test_cli.py`: con pendientes tras el turno se escribe el aviso; sin
pendientes, no.
