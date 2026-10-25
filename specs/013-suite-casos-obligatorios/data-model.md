# Data Model: Suite de casos obligatorios y README

**Feature**: [spec.md](spec.md) · **Research**: [research.md](research.md)

Todo vive en los tests; no hay cambios en `src/`.

## Llamada (`tests/escenarios/registro.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `herramienta` | texto | Nombre corto (`buscar_cliente`, `iniciar_disputa`, …; sin prefijo `mcp__core-bancario__`) |
| `argumentos` | dict | El `input` del `ToolUseBlock` |
| `respuesta` | dict o `None` | El contrato del core leído con `leer_respuesta`; `None` si no llegó o no se pudo leer |
| `negada` | `str` o `None` | Código del control si el `tool_use_id` está en las negaciones del turno |

Propiedades: `ok` (respuesta con `ok: true`), `codigo` (código de error del core o `None`).
Solo se registran llamadas del agente principal, en el orden de los `ToolUseBlock`.

## Registro (`tests/escenarios/registro.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `llamadas` | lista de `Llamada` | En orden |
| `pendientes` | dict | Copia de `controles.estado.pendientes` al terminar |
| `estado` | texto | Estado del turno según `procesar_turno` (`completado`, …) |
| `texto` | texto | Respuesta final (solo para diagnóstico; ningún caso afirma sobre ella) |

Consultas: `de(herramienta)` → llamadas de esa herramienta; `primera()` → primera llamada;
`escalamientos(causa)` → escalamientos exitosos con esa causa.

Funciones: `armar_registro(mensajes, estado_controles, inicio_negaciones, resultado)` pura y
probada sin API (`resultado` es el `ResultadoTurno` de `procesar_turno`); `conversar(mensaje, entorno=None)` corre el turno real y devuelve el `Registro`.

## Caso (`tests/escenarios/casos.py`)

Diccionario `MENSAJES: dict[str, str]` con una clave por caso (`mensaje_de_ejemplo`,
`persona`, `homonimos`, `sin_identidad`, `falla_transitoria`, `fuera_de_politica`). Los
mensajes que llevan dato de verificación se arman con una función que lo lee del core
(`mensaje(caso)`), y `MENSAJES` guarda la plantilla sin el dato para la comparación con el
prompt.
