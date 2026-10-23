# Data Model: Bloqueo y escalamiento (issue #7)

Los datos del #4 no cambian. `Tarjeta.estado` es el estado **inicial**; el efectivo lo da el
registro de bloqueos.

## RegistroBloqueos (Contexto, campo `bloqueos`)

- Estado: `dict[tarjeta_id, motivo]` de los bloqueos de la sesión; vacío al arrancar.
- `estado_de(tarjeta)`: `"bloqueada"` si `tarjeta.estado == "bloqueada"` o `tarjeta.id` está
  en el registro; si no, `"activa"`.
- `bloquear(tarjeta, motivo) -> bool`: registra el bloqueo y devuelve si **ya** estaba
  bloqueada antes del llamado. Nunca desbloquea.

```text
activa ──bloquear──> bloqueada ──bloquear──> bloqueada (ya_estaba_bloqueada = true)
```

## Escalamiento (dataclass inmutable)

| Campo | Tipo | Nota |
|---|---|---|
| `id` | texto | `ESC-0001`, `ESC-0002`, ... (contador propio) |
| `causa` | texto | `persona_solicitada`, `umbral`, `fuera_de_politica`, `intentos_agotados`, `otra` |
| `cliente_id` | texto o `None` | `None` solo con `persona_solicitada` |
| `transacciones` | tupla de ids | sin repetidos, en el orden recibido |
| `acciones_realizadas` | texto | hasta 1000 caracteres |
| `accion_recomendada` | texto | hasta 500 caracteres |
| `estado` | texto | `pendiente_analista` |

## RegistroEscalamientos (Contexto, campo `escalamientos`)

- `registrar(causa, cliente_id, transacciones, acciones, recomendada) -> Escalamiento`.
- `todos() -> list[Escalamiento]` (para tests y, después, para el hook del #10).

## Reglas de validación

| Entrada | Regla | Error |
|---|---|---|
| `cliente_id`, `ultimos4`, `motivo` (bloqueo) | textos no vacíos; `ultimos4` `^[0-9]{4}$`; motivo hasta 500 | validación `PARAMETRO_INVALIDO` |
| tarjeta del cliente | `tarjetas_de` no vacío | validación `NO_ENCONTRADO` |
| `causa`, `acciones_realizadas`, `accion_recomendada` | obligatorios, no vacíos | validación `PARAMETRO_INVALIDO` (nombra todos los faltantes) |
| `causa` | en la lista cerrada | validación `PARAMETRO_INVALIDO` |
| `cliente_id` (escalamiento) | obligatorio salvo `persona_solicitada`; existe | `PARAMETRO_INVALIDO` / `NO_ENCONTRADO` |
| `transacciones` | lista o lista JSON de textos; obligatoria con `umbral` y `fuera_de_politica`; cada una existe y es del cliente | `PARAMETRO_INVALIDO` / `NO_ENCONTRADO` |

## Cambios heredados

- `Politica.limite_dias(transaccion) -> int`.
- `RegistroDisputas`: contador propio para `CASO-NNNN`.
