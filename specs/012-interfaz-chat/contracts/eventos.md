# Contrato: eventos visibles

**Feature**: [../spec.md](../spec.md) · **Modelo**: [../data-model.md](../data-model.md)

Cómo `LectorEventos` convierte cada llamada de un turno en un evento. Se evalúa en este orden:

1. Si la llamada fue negada por un control (`tool_use_id` en las negaciones del turno) →
   evento `negacion`, aunque llegue un resultado.
2. Si no, según la herramienta y la respuesta del core leída con `leer_respuesta`. La
   delegación es la excepción: su resultado es el texto del subagente, no el contrato del
   core, y se juzga solo por `is_error` del `ToolResultBlock`.
3. Una respuesta del core que no se puede leer, o una llamada sin resultado al cerrar el
   turno → evento `falla` (nunca `exito`).

## Tabla

| Llamada | Respuesta | Tipo / resultado | Título | Detalle |
|---|---|---|---|---|
| verificar identidad | `ok: true`, `verificado: true` | `identidad` / exito | Identidad verificada | id del cliente |
| verificar identidad | `ok: false` (`VERIFICACION_FALLIDA`, `INTENTOS_AGOTADOS`, …) | `identidad` / falla | No se pudo verificar la identidad | motivo de negocio según el código |
| bloquear tarjeta | `ok: true` | `bloqueo` / exito | Tarjeta bloqueada | `•••• NNNN` (y "ya estaba bloqueada" si aplica) |
| iniciar disputa | `ok: true` | `disputa` / exito | Disputa iniciada | caso, transacción y monto del core en pesos |
| iniciar disputa | `ok: false`, `FUERA_DE_POLITICA` | `rechazo_politica` / negado | Disputa fuera de la política del banco | transacción; "requiere un analista" |
| iniciar disputa | `ok: false`, `REQUIERE_ANALISTA` | `rechazo_politica` / negado | Disputa por encima del umbral | transacción; "requiere un analista" |
| escalar a analista | `ok: true` | `escalamiento` / exito | Caso escalado a un analista | id del escalamiento y motivo (ver causas) |
| delegar en el analista de transacciones | `is_error` falso o ausente | `analisis` / exito | Análisis de transacciones realizado | — (no se expone el razonamiento del subagente) |
| delegar en el analista de transacciones | `is_error` verdadero | `falla` / falla | No se pudo completar: Análisis de transacciones | — |
| cualquiera sobre productos o delegación | negada por control | `negacion` / negado | Operación negada por un control del banco | operación y razón (ver razones) |
| cualquiera con evento | `ok: false` con otro código, o ilegible | `falla` / falla | No se pudo completar: *operación* | "error temporal del sistema" si es transitorio; si no, "datos inválidos" |
| buscar cliente, consultar transacciones | `ok: true` | sin evento | — | — |

## Nombres de negocio

- **Operación**: consultar transacciones → "Consulta de transacciones"; iniciar disputa →
  "Disputa"; bloquear tarjeta → "Bloqueo de tarjeta"; delegación → "Análisis de
  transacciones"; verificar identidad → "Verificación de identidad"; escalar → "Escalamiento".
- **Causas de escalamiento**: `persona_solicitada` → "el cliente pidió hablar con una
  persona"; `umbral` → "el monto supera el umbral de disputa automática"; `fuera_de_politica`
  → "el caso está fuera de la política del banco"; `intentos_agotados` → "se agotaron los
  intentos de verificación"; `otra` → "otro motivo".
- **Razones de negación** (por código del control): `SIN_IDENTIDAD` → "la identidad del
  cliente no está verificada"; `CLIENTE_DISTINTO` → "el producto no es del cliente
  verificado"; `TRANSACCION_NO_CONFIRMADA` → "no se pudo confirmar que la transacción sea del
  cliente verificado"; `REQUIERE_ANALISTA` → "el monto supera el umbral de disputa automática
  y requiere un analista"; `CONTEXTO_INCOMPLETO`, `SUBAGENTE_NO_PERMITIDO`,
  `SEGUNDO_PLANO_NO_PERMITIDO` → "la solicitud de análisis no cumplió las condiciones";
  `FALLA_CONTROL` o código desconocido → "no se pudo confirmar la operación".

## Garantías

- Ningún evento `exito` sin `ok: true` del core (SC-002); se prueba con cada fila.
- Cada llamada produce como máximo un evento, aunque el hook `Stop` haga repetir el cierre.
- Los detalles solo usan datos de la llamada o de la respuesta del core: ids ficticios,
  últimos 4 dígitos y montos del core; nunca textos del modelo.
