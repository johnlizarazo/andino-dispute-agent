# Data Model: Transacciones y disputas (issue #6)

`Cliente`, `Tarjeta` y `Transaccion` son las del
[data-model del #4](../004-datos-errores-fallas/data-model.md); los datos no cambian. Se
agregan:

## Repositorio (cambios)

| Miembro | Tipo | Nota |
|---|---|---|
| `hoy` | `date` | el inyectado o `date.today()`; base de rangos y antigüedad |
| `tarjetas_de(cliente_id, ultimos4)` | `list[Tarjeta]` | solo tarjetas de ese cliente |

## Politica (métodos nuevos)

| Método | Regla |
|---|---|
| `requiere_analista(monto)` | `monto > umbral_disputa_automatica` ($500.000 se abre) |
| `cubre(transaccion, hoy)` | `(hoy − fecha).days ≤ 120` si `pais == "CO"`; `≤ 90` en otro caso |

## Caso (dataclass inmutable)

| Campo | Tipo | Nota |
|---|---|---|
| `id` | texto | `CASO-0001`, `CASO-0002`, ... |
| `transaccion_id` | texto | |
| `monto` | entero | copiado de la transacción del core |
| `motivo` | texto | hasta 500 caracteres, recortado |
| `estado` | texto | `abierta` |

## RegistroDisputas (en el Contexto, campo `disputas`)

- Estado: `dict[transaccion_id, Caso]` y un contador; vacío al arrancar.
- `caso_de(transaccion_id)`: el caso o `None`.
- `abrir(transaccion, motivo)`: crea el siguiente `CASO-NNNN`; si ya existe caso para esa
  transacción, `ValueError`.
- Una transacción tiene como máximo un caso (SC-005). Las disputas rechazadas no crean caso.

## Cobro consultado (respuesta)

| Campo | Tipo |
|---|---|
| `transaccion_id` | texto |
| `fecha` | texto `AAAA-MM-DD` |
| `monto` | entero |
| `comercio` | texto |
| `pais` | texto (2 letras) |
| `caso_disputa` | texto o `null` |

Orden: fecha descendente y, a igual fecha, `transaccion_id` ascendente.

## Validaciones de entrada

| Entrada | Regla | Error |
|---|---|---|
| `cliente_id` | texto no vacío | validación `PARAMETRO_INVALIDO` |
| `ultimos4` | `^[0-9]{4}$` | validación `PARAMETRO_INVALIDO` |
| `fecha_desde`, `fecha_hasta` | opcionales; `^[0-9]{4}-[0-9]{2}-[0-9]{2}$` y fecha real | validación `PARAMETRO_INVALIDO` |
| rango | desde ≤ hasta ≤ hoy, como máximo 365 días | validación `PARAMETRO_INVALIDO` |
| tarjeta del cliente | `tarjetas_de` no vacío | validación `NO_ENCONTRADO` |
| `transaccion_id` | texto no vacío; existe | validación `PARAMETRO_INVALIDO` / `NO_ENCONTRADO` |
| `motivo` | texto no vacío, hasta 500 caracteres | validación `PARAMETRO_INVALIDO` |
