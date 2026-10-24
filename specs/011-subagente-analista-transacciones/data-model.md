# Data Model: Subagente `analista-transacciones`

Fundamento en [research.md](research.md) R2 y R4. Todo en memoria; ninguna entidad nueva en
el estado de la conversación salvo las negaciones del control de delegación.

## Contexto de delegación (bloque `<contexto>` en el prompt de la delegación)

| Campo | Tipo | Regla |
|---|---|---|
| `cliente_id` | `str` | "igual al cliente verificado (sin espacios)" |
| `ultimos4` | `str` | "exactamente 4 dígitos" |
| `fecha_desde` | `str` | "`AAAA-MM-DD` válida" |
| `fecha_hasta` | `str` | "`AAAA-MM-DD` válida, `fecha_desde <= fecha_hasta`" |
| `montos_reportados` | `list[int]` | "enteros positivos; puede ir vacía" |

Un campo de más no invalida el bloque (se ignora).

## Resultado del análisis (bloque `<analisis>` en la respuesta del subagente)

| Campo | Tipo | Regla |
|---|---|---|
| `transacciones` | `list[ClasificacionTransaccion]` | solo transacciones devueltas por el core |
| `montos_no_encontrados` | `list[int]` | montos reportados sin transacción con ese monto |
| `error` | `str` (opcional) | si la consulta falló; entonces `transacciones` va vacía |

### ClasificacionTransaccion

| Campo | Tipo | Regla |
|---|---|---|
| `transaccion_id` | `str` | id del core |
| `fecha` | `str` | `AAAA-MM-DD` |
| `monto` | `int` | pesos |
| `clasificacion` | `str` | `disputable`, `sobre_umbral` o `fuera_de_politica`; precedencia: primero fuera de política, luego sobre umbral, si no disputable |
| `razon` | `str` | una frase |

## Códigos de negación nuevos (control de delegación)

| Código | Cuándo |
|---|---|
| `SUBAGENTE_NO_PERMITIDO` | la delegación pide otro tipo de subagente |
| `CONTEXTO_INCOMPLETO` | falta el bloque, no es JSON o algún campo falta o es inválido |

Reutilizados del #9: `SIN_IDENTIDAD`, `CLIENTE_DISTINTO`, `FALLA_CONTROL`.
