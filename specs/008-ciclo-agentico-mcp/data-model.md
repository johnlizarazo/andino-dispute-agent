# Data Model: Ciclo agéntico y conexión al MCP (issue #8)

## ResultadoTurno (dataclass inmutable)

| Campo | Tipo | Nota |
|---|---|---|
| `estado` | texto | `completado`, `salvaguarda`, `falla_servicio`, `error` |
| `texto` | texto | texto final del agente (unión de los `TextBlock` del turno) |
| `herramientas` | tupla de textos | nombres de herramientas usadas en el turno, en orden (para tests y registro) |
| `detalle` | texto o `None` | detalle técnico solo para el registro; nunca se muestra al cliente |

## Clasificación del resultado

| Condición del `ResultMessage` | `estado` | Qué ve el cliente |
|---|---|---|
| `subtype == "success"` y no `is_error` | `completado` | el texto del agente |
| `subtype == "error_max_turns"` o `terminal_reason == "max_turns"` | `salvaguarda` | aviso de que no se pudo terminar y opción de pedir una persona |
| `is_error` con `api_error_status` | `falla_servicio` | aviso de problema temporal; puede reintentar |
| otro | `error` | aviso genérico sin datos técnicos |

## Opciones del agente

| Opción | Valor |
|---|---|
| `tools` | `[]` |
| `allowed_tools` | `mcp__core-bancario__` + cada una de las 6 herramientas |
| `permission_mode` | `dontAsk` |
| `mcp_servers` | solo `core-bancario` por stdio (`sys.executable -m core_bancario_mcp`) |
| `strict_mcp_config` | `True` |
| `setting_sources` | `[]` |
| `system_prompt` | `prompts.PROMPT_SISTEMA` |
| `model` | `ANDINO_MODELO` o `claude-sonnet-5-5` |
| `max_turns` | `MAXIMO_PASOS_POR_TURNO` = 25 (salvaguarda) |

## Variables de entorno

| Variable | Obligatoria | Uso |
|---|---|---|
| `ANTHROPIC_API_KEY` | sí | credencial del servicio del modelo; nunca se imprime |
| `ANDINO_MODELO` | no | modelo; por omisión `claude-sonnet-5-5` |
| `CORE_BANCARIO_FALLAS` | no | se pasa al core para inyectar fallas |
