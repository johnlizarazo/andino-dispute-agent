# Contrato: controles del agente (`src/agente_disputas/controles.py`)

Fundamento en [research.md](../research.md) R1 a R7; entidades en
[data-model.md](../data-model.md).

## Registro en las opciones

```text
hooks = {
  "PreToolUse":  [HookMatcher(matcher="mcp__core-bancario__consultar_transacciones|"
                                      "mcp__core-bancario__iniciar_disputa|"
                                      "mcp__core-bancario__bloquear_tarjeta",
                              hooks=[controles.antes_de_herramienta], timeout=10)],
  "PostToolUse": [HookMatcher(matcher="mcp__core-bancario__verificar_identidad",
                              hooks=[controles.despues_de_verificar], timeout=10)],
}
```

- Ningún matcher para `buscar_cliente` ni `escalar_a_analista` (exentas, FR-005).
- `crear_opciones(entorno, controles=None)` agrega `hooks`, `allowed_tools` con las 6
  herramientas y `disallowed_tools=[]`; el resto de opciones no cambia.

## `antes_de_herramienta(input, tool_use_id, context)` — PreToolUse

Autoriza devolviendo `{}` (sin decisión: sigue el flujo normal de permisos, donde la
herramienta ya está en `allowed_tools`). Niega con:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse",
  "permissionDecision": "deny", "permissionDecisionReason": "<razón>"}}
```

| Caso (en este orden) | Código | Razón (texto orientativo) |
|---|---|---|
| sin cliente verificado | `SIN_IDENTIDAD` | "Primero verifica la identidad del cliente con verificar_identidad." |
| consultar/bloquear con `cliente_id` ausente, no texto o distinto del verificado | `CLIENTE_DISTINTO` | "Solo puedes operar sobre productos del cliente verificado en esta conversación." |
| disputar con `transaccion_id` ausente, no texto, inexistente o de otro titular | `TRANSACCION_NO_CONFIRMADA` | "No se pudo confirmar que esa transacción pertenezca al cliente verificado." |
| disputar con monto real > umbral | `REQUIERE_ANALISTA` | "Esta disputa supera $500.000 y requiere un analista humano: escala el caso." |
| no se pudo cargar o consultar el dato, nombre de herramienta inesperado o cualquier excepción | `FALLA_CONTROL` | "No se pudo confirmar la operación en este momento; no se realizó." |

- Monto exactamente 500000 → autoriza.
- Cada negación agrega una `Negacion` a `estado.negaciones`.
- Nunca lanza: toda excepción interna termina en `FALLA_CONTROL`.

## `despues_de_verificar(input, tool_use_id, context)` — PostToolUse

- Lee `tool_response` con `leer_respuesta` (formas aceptadas en research R4).
- Si es `{"ok": true, "datos": {"verificado": true, "cliente_id": X}}` con `X` texto no vacío
  igual al `cliente_id` de `tool_input` (sin espacios) → `estado.cliente_verificado = X`.
- En cualquier otro caso no cambia el estado. Devuelve siempre `{}` y nunca lanza.

## `Controles.desde_entorno(entorno)`

- Carga `Repositorio()`; si falla, controles sin datos (toda disputa → `FALLA_CONTROL`).
- Inyector: `InyectorFallas(entorno.get("CORE_BANCARIO_FALLAS"))`; la operación
  `control_transaccion` hace fallar la consulta de la transacción. Una configuración inválida
  ya impide arrancar al core; en el control, deja los controles sin datos (falla cerrada).

## Tests deterministas (sin API) — `test_controles.py`

Se llaman los callbacks con diccionarios de entrada construidos a mano y `asyncio.run`:

1. Sin verificar: las 3 herramientas se niegan con `SIN_IDENTIDAD` (caso de prueba del issue:
   `iniciar_disputa` con `TRX-001`).
2. Verificación exitosa de CLI-001 → `consultar` y `bloquear` con CLI-001 autorizan; con
   CLI-002 se niegan (`CLIENTE_DISTINTO`), y la razón no contiene "CLI-002".
3. Verificación fallida (`ok: false`), ilegible (`None`, `"x"`, `[]`) o para otro `cliente_id`
   → no registra.
4. Segunda verificación exitosa (CLI-002) reemplaza a la primera.
5. Disputa: `TRX-001` (180000, CLI-001) autoriza; `TRX-002` (1250000) → `REQUIERE_ANALISTA`;
   con CLI-002 verificado, `TRX-004` (500000) autoriza y `TRX-001` → `TRANSACCION_NO_CONFIRMADA`
   igual que `TRX-999`.
6. Falla cerrada: inyector `control_transaccion:1` → `FALLA_CONTROL`; repositorio que no carga →
   `FALLA_CONTROL`; `buscar_transaccion` que lanza → `FALLA_CONTROL`; `tool_input` no dict →
   `FALLA_CONTROL` o la negación que corresponda, nunca autoriza.
7. `leer_respuesta` con cada forma aceptada y con formas rechazadas.
8. Argumentos con espacios (`" CLI-001 "`, `" TRX-001 "`) se tratan como el core (sin espacios).

En `test_configuracion.py`:

9. Matchers con los nombres completos exactos; sin matcher para las exentas.
10. Las 6 herramientas en `allowed_tools`, `disallowed_tools` vacío.
11. Sin prompt (FR-009): `replace(opciones, system_prompt=None)` y el callback registrado en
    `opciones.hooks["PreToolUse"]` sigue negando la disputa sin verificación.
12. Cada `crear_opciones` crea un estado nuevo (FR-002).
