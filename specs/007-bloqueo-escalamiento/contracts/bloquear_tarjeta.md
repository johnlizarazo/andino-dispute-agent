# Contrato: `bloquear_tarjeta`

Fundamento en [research.md R1 y R2](../research.md).

## Parámetros (tipo `Texto`, con `None` por omisión)

| Parámetro | Formato |
|---|---|
| `cliente_id` | id del cliente verificado |
| `ultimos4` | 4 dígitos |
| `motivo` | por qué se sospecha fraude; hasta 500 caracteres |

No existe parámetro ni paso de aprobación (regla 3).

## Respuestas (en este orden de evaluación)

1. Transitorio `FALLA_TRANSITORIA` (`bloquear_tarjeta:N`); no bloquea.
2. Validación `PARAMETRO_INVALIDO`: tipo no texto, vacío, `ultimos4` mal formado, motivo de
   más de 500 caracteres.
3. Validación `NO_ENCONTRADO`: no hay tarjeta con esos últimos 4 para ese cliente (mismo
   mensaje que `consultar_transacciones`).
4. Éxito: `{"ok": true, "datos": {"ultimos4": "4821", "estado": "bloqueada",
   "ya_estaba_bloqueada": false}}`.

## Descripción publicada (esencia)

Bloquea de inmediato una tarjeta del cliente (por `cliente_id` y últimos 4) por sospecha de
fraude. Requiere la identidad verificada del titular. No requiere ni espera la aprobación de
un analista. Si la tarjeta ya estaba bloqueada, responde con `ya_estaba_bloqueada`: no es un
error.

## Tests (`test_bloqueo_escalamiento.py`)

- CLI-001 `4821` → bloqueada, `ya_estaba_bloqueada` falso; `contexto.bloqueos.estado_de`
  de TAR-001 pasa a `bloqueada`.
- Bloquear otra vez la misma → éxito con `ya_estaba_bloqueada` verdadero.
- CLI-004 `9012` (bloqueada en los datos) → éxito con `ya_estaba_bloqueada` verdadero.
- CLI-002 `4821` y CLI-999 `4821` → `NO_ENCONTRADO` con el mismo mensaje.
- Motivo vacío, de 501 caracteres o numérico, `ultimos4` `48a1` → `PARAMETRO_INVALIDO`, sin
  bloquear.
- Una tarjeta bloqueada se puede seguir consultando y disputando (no cambia el #6).
