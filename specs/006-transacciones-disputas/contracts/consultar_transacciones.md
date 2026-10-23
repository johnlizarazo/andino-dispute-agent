# Contrato: `consultar_transacciones`

Fundamento en [research.md R2 y R4](../research.md).

## Parámetros (tipo `Texto`, todos con `None` por omisión)

| Parámetro | Obligatorio | Formato |
|---|---|---|
| `cliente_id` | sí | id devuelto por `buscar_cliente` |
| `ultimos4` | sí | 4 dígitos |
| `fecha_desde` | no | `AAAA-MM-DD`; por omisión, `fecha_hasta` − 29 días (30 días con ambos extremos) |
| `fecha_hasta` | no | `AAAA-MM-DD`; por omisión, hoy |

## Respuestas (en este orden de evaluación)

1. Transitorio `FALLA_TRANSITORIA` (`consultar_transacciones:N`).
2. Validación `PARAMETRO_INVALIDO`: tipo no texto, `cliente_id` vacío, `ultimos4` mal
   formado, fecha mal formada o imposible, desde > hasta, hasta en el futuro, más de 365 días.
3. Validación `NO_ENCONTRADO`: no hay tarjeta con esos últimos 4 para ese cliente (mismo
   mensaje si el cliente no existe).
4. Éxito: `{"ok": true, "datos": [{"transaccion_id", "fecha", "monto", "comercio", "pais",
   "caso_disputa"}, ...]}`, lista vacía si no hay cobros en el rango.

## Descripción publicada (esencia)

Lista los cobros de una tarjeta del cliente (por `cliente_id` y últimos 4) en un rango de
fechas `AAAA-MM-DD` (por omisión, los últimos 30 días). Requiere la identidad verificada del
titular. Úsala para ubicar con el cliente el cobro que no reconoce antes de disputarlo. Un
cobro con `caso_disputa` ya tiene una disputa abierta.

## Tests (`test_transacciones.py`, "hoy" fijo)

- Tarjeta 4821 de CLI-001, rango ayer–ayer → TRX-001 y TRX-002 (para 3 "hoy" distintos).
- Sin rango → los cobros de hoy y los 29 días anteriores (un cobro de hace 29 días entra y uno de hace 30 no, con datos en `tmp_path`), ordenados de más reciente a más antiguo.
- Rango sin cobros → `exito([])`.
- Tarjeta bloqueada (CLI-004, `9012`) → sus cobros se listan (TRX-007).
- Solo `fecha_desde` o solo `fecha_hasta` → se completa la otra.
- `20261023`, `2026-W43-5`, `2026-02-30`, desde > hasta, hasta = mañana, 366 días, fecha
  numérica → validación `PARAMETRO_INVALIDO`.
- Tarjeta de otro cliente (4821 con CLI-002) y cliente inexistente → `NO_ENCONTRADO` con el
  mismo mensaje.
- Cobro con caso abierto → `caso_disputa` con el id; sin caso → `null`.
- Ningún cobro trae claves distintas de las del contrato.
