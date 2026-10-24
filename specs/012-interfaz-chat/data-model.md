# Data Model: Interfaz de chat

**Feature**: [spec.md](spec.md) · **Research**: [research.md](research.md)

Todo vive en memoria y dura lo que dura la conversación; no hay persistencia.

## Evento (nuevo, `eventos.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `tipo` | texto, uno de `identidad`, `bloqueo`, `disputa`, `rechazo_politica`, `escalamiento`, `analisis`, `negacion`, `falla` | Tabla de [contracts/eventos.md](contracts/eventos.md) |
| `resultado` | `exito`, `negado` o `falla` | Nunca `exito` si el core no respondió `ok: true` (SC-002) |
| `titulo` | texto | Lenguaje de negocio; sin nombres de herramientas (FR-008) |
| `detalle` | texto o vacío | Datos de negocio: últimos 4, ids de caso, monto en pesos del core, motivo o razón |

Inmutable (`dataclass(frozen=True)`).

## LectorEventos (nuevo, `eventos.py`)

Lee los mensajes de un turno y produce eventos en orden.

- Estado: llamadas pendientes `tool_use_id → (herramienta, argumentos)` y los
  `tool_use_id` negados por los controles en este turno.
- `leer(mensaje) -> list[Evento]`: un `ToolUseBlock` queda pendiente; un `ToolResultBlock`
  cierra su llamada y produce su evento (o ninguno, según la tabla).
- `cerrar() -> list[Evento]`: al terminar el turno, las llamadas que quedaron sin resultado
  producen `negacion` si fueron negadas o `falla` si no.
- Fuente de negaciones: `Controles.estado.negaciones` (solo las agregadas durante el turno).

## Negacion (modificada, `controles.py`)

| Campo | Cambio |
|---|---|
| `herramienta` | sin cambio |
| `codigo` | sin cambio |
| `tool_use_id` | **nuevo**, `str | None`: el que recibe el hook `PreToolUse`; `None` si no llega |

## SesionChat (nuevo, `sesion.py`)

Una por conversación de la interfaz.

- Dueña de sus `Controles` (estado nuevo) y de un trabajador que abre el
  `ClaudeSDKClient` y atiende una cola de mensajes (research R3).
- `iniciar() -> str | None`: arranca el trabajador y espera el core; devuelve un aviso si la
  credencial falta o el core no conecta (FR-011), `None` si quedó lista.
- `turno(texto, al_evento) -> str`: encola el mensaje; por cada evento llama `al_evento` en
  orden; devuelve la respuesta o el aviso final (FR-009), seguido del aviso de escalamiento
  pendiente si quedó alguno.
- `cerrar()`: termina el trabajador y libera el cliente.

Transiciones: `creada → lista` (core conectado) · `creada → no disponible` (sin credencial
o sin core) · `lista → cerrada` (fin del chat o sesión perdida, con `AVISO_SESION`).
