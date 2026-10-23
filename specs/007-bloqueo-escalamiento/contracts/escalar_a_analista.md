# Contrato: `escalar_a_analista`

Fundamento en [research.md R3, R4 y R5](../research.md).

## Parámetros (con `None` por omisión)

| Parámetro | Tipo | Formato |
|---|---|---|
| `causa` | `Texto` | `persona_solicitada`, `umbral`, `fuera_de_politica`, `intentos_agotados`, `otra` |
| `cliente_id` | `Texto` | obligatorio salvo `persona_solicitada` |
| `transacciones` | `ListaTexto` | ids; obligatoria y no vacía con `umbral` y `fuera_de_politica` |
| `acciones_realizadas` | `Texto` | lo que el agente ya hizo; hasta 1000 caracteres |
| `accion_recomendada` | `Texto` | qué debe hacer el analista; hasta 500 caracteres |

No hay parámetro de monto: el core completa monto, fecha, comercio y caso de cada
transacción (regla 2).

## Respuestas (en este orden de evaluación)

1. Transitorio `FALLA_TRANSITORIA` (`escalar_a_analista:N`); no registra nada.
2. Validación `PARAMETRO_INVALIDO` por tipo (texto no texto; transacciones que no son lista
   ni lista JSON de textos).
3. Validación `PARAMETRO_INVALIDO` por faltantes: nombra todos los de `causa`,
   `acciones_realizadas`, `accion_recomendada` que falten.
4. Validación `PARAMETRO_INVALIDO`: causa fuera de la lista (el mensaje lista las válidas).
5. Validación `PARAMETRO_INVALIDO`: largos excedidos.
6. Cliente: falta con una causa que lo exige → `PARAMETRO_INVALIDO`; no existe →
   `NO_ENCONTRADO`.
7. Transacciones: faltan con `umbral` o `fuera_de_politica` → `PARAMETRO_INVALIDO`; una no
   existe → `NO_ENCONTRADO`; una no es del cliente → `PARAMETRO_INVALIDO`.
8. Éxito: registra el `Escalamiento` completo para el analista (ver
   [data-model.md](../data-model.md)) y responde al agente solo:

```json
{"ok": true, "datos": {"escalamiento_id": "ESC-0001", "causa": "umbral",
                       "estado": "pendiente_analista", "cantidad_transacciones": 1}}
```

La respuesta nunca incluye montos, fechas, comercios ni el nombre del cliente (ajuste C1:
escalar está exento de identidad verificada y no puede servir para consultar productos).

Ningún error registra el escalamiento.

## Descripción publicada (esencia)

Escala el caso a un analista humano con un resumen estructurado. No requiere identidad
verificada. Si el cliente pide hablar con una persona, escala de inmediato con causa
`persona_solicitada`, aunque no esté identificado. Úsala también cuando el core responde
`REQUIERE_ANALISTA` (causa `umbral`), `FUERA_DE_POLITICA` (`fuera_de_politica`) o
`INTENTOS_AGOTADOS` (`intentos_agotados`). Envía solo los ids de las transacciones: el core
completa los montos.

## Tests (`test_bloqueo_escalamiento.py`)

- Causa `umbral`, CLI-001, `["TRX-002"]` → respuesta exactamente `{"escalamiento_id":
  "ESC-0001", "causa": "umbral", "estado": "pendiente_analista", "cantidad_transacciones": 1}`;
  el registro guardado tiene nombre del cliente, monto 1250000 y total 1250000; un segundo →
  `ESC-0002`.
- Ninguna respuesta de éxito contiene claves distintas de las cuatro del contrato.
- `persona_solicitada` sin cliente ni transacciones → éxito; el registro tiene cliente `None`.
- `intentos_agotados` con cliente y sin transacciones → éxito; sin cliente → validación.
- Faltan `causa` y `accion_recomendada` → un error que nombra ambos.
- Causa `urgente` → validación con las causas válidas.
- `umbral` sin transacciones → validación.
- `TRX-999` → `NO_ENCONTRADO`; `TRX-004` con CLI-001 → validación (no es del cliente).
- Transacciones repetidas → una vez (`cantidad_transacciones` 1; total sin duplicar en el registro).
- Transacción con disputa abierta → el registro guarda su `caso_disputa`.
- `transacciones` como texto JSON `'["TRX-002"]'` → aceptado; como `"TRX-002"`, número, objeto
  o `[1]` → validación.
- Acciones de 1001 caracteres o recomendación de 501 → validación.
- Ningún error deja un escalamiento registrado (`contexto.escalamientos.todos()` vacío).
