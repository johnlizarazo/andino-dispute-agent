# Research: Ciclo agéntico y conexión al MCP (issue #8)

API verificada por introspección de `claude-agent-sdk` 0.2.168 instalado (campos de
`ClaudeAgentOptions`, tipos de mensajes y docstrings).

## R1. Estructura del paquete

- **Decision**: en `src/agente_disputas/`:
  - `prompts.py`: `PROMPT_SISTEMA` y `VERSION_PROMPT`.
  - `configuracion.py`: `HERRAMIENTAS` (las 6 del core), `crear_opciones(entorno)` y la
    validación de la credencial.
  - `ciclo.py`: `ResultadoTurno`, `clasificar(resultado)` y `procesar_turno(mensajes)`,
    puros sobre los mensajes del SDK.
  - `cli.py` y `__main__.py`: la línea de comandos (`python -m agente_disputas`).
  - Tests junto a cada módulo; escenarios `e2e` en `tests/escenarios/` (rule `tests.md`).
- **Rationale**: separa lo determinista (configuración, clasificación del turno) de la E/S
  (SDK y terminal), así casi todo se prueba sin API.

## R2. "Continúa o termina según la razón de parada" sobre el SDK

- **Hallazgo**: `ClaudeSDKClient.query(...)` + `receive_response()` emite, dentro de un turno,
  `AssistantMessage` (con `stop_reason`: `tool_use` mientras el modelo pide herramientas,
  `end_turn` al terminar), `UserMessage` con los resultados de herramientas y, al final, un
  `ResultMessage` (`subtype`, `stop_reason`, `terminal_reason`, `is_error`,
  `api_error_status`). El SDK ejecuta las herramientas y vuelve al modelo mientras la razón de
  parada sea `tool_use`.
- **Decision**: `procesar_turno` consume los mensajes del turno hasta el `ResultMessage` sin
  contar ni buscar palabras, junta el texto de los `TextBlock` y delega en `clasificar`:
  - `subtype == "success"` y no `is_error` → **completado** (el modelo indicó fin de turno).
  - `subtype == "error_max_turns"` o `terminal_reason == "max_turns"` → **salvaguarda**.
  - `is_error` con `api_error_status` (429, 500, 529…) → **falla del servicio** (temporal).
  - cualquier otro error → **error** con detalle técnico solo para el registro.
- `max_turns` (`MAXIMO_PASOS_POR_TURNO = 25`) es la salvaguarda documentada (FR-006).
- **Alternatives considered**: implementar el ciclo de herramientas a mano con la API de
  mensajes (duplica lo que el SDK ya hace y el issue pide `ClaudeSDKClient`).

## R3. Solo las 6 herramientas, sin entorno ni permisos interactivos (FR-008)

- **Decision** en `crear_opciones`:
  - `tools=[]`: desactiva todas las herramientas propias de Claude Code (docstring: "Disable
    all built-in tools").
  - `allowed_tools=[f"mcp__core-bancario__{n}" for n in HERRAMIENTAS]`: las 6 preaprobadas.
  - `permission_mode="dontAsk"`: "Don't prompt for permissions; deny if not pre-approved".
  - `mcp_servers={"core-bancario": {...stdio...}}` con `strict_mcp_config=True` (ignora el
    `.mcp.json` del proyecto, que trae también el servidor de GitHub).
  - `setting_sources=[]`: aísla de los settings del disco (hooks, permisos y plugins del
    desarrollador no se mezclan con el agente).
- **Rationale**: es una garantía por configuración, verificable con un test que inspecciona
  las opciones sin llamar a la API.

## R4. Servidor, credencial y modelo (FR-007, FR-010, FR-010b)

- **Servidor**: `{"type": "stdio", "command": sys.executable, "args": ["-m",
  "core_bancario_mcp"]}`, con `env` que pasa `CORE_BANCARIO_FALLAS` solo si está definida. Usar
  el mismo intérprete evita el bloqueo de `.venv` en Windows que obligó a `--no-sync`.
- **Credencial**: `configuracion.validar_credencial(entorno)` exige `ANTHROPIC_API_KEY` no
  vacía antes de conectar; si falta, la CLI dice qué variable falta y termina con código 1.
  La clave nunca se imprime ni se copia a otra estructura; el SDK la hereda del entorno.
  Exigirla impide que el CLI subyacente use otra sesión del equipo.
- **Modelo**: `ANDINO_MODELO` o `claude-sonnet-5-5` por omisión.

## R5. Errores reintentables y fallas del SDK (FR-011 a FR-013)

- **Decision**:
  - Errores del core (`reintentable`): el prompt indica reintentar la misma llamada hasta 2
    veces y, si persiste, informar sin detalles técnicos y ofrecer escalar; ante
    `reintentable: false`, no repetir y actuar según `tipo`. Se verifica con un escenario
    `e2e` con `CORE_BANCARIO_FALLAS`.
  - Fallas del servicio del modelo: `clasificar` las marca como temporales y la CLI muestra
    un aviso y sigue esperando mensajes.
  - Excepciones del SDK (`CLINotFoundError`, `CLIConnectionError`, `ProcessError`): si ocurren
    al conectar, mensaje claro y salida 1; durante la conversación, mensaje claro y fin de la
    sesión (el proceso ya no sirve).
- **Rationale**: la garantía de reintentos es por instrucción (declarado en la spec); lo
  determinista es que ningún error termina en traza.

## R6. Arranque del core y verificación

- **Decision**: tras `connect()`, `cliente.get_mcp_status()`; si `core-bancario` no está
  `connected`, la CLI informa ("el core bancario no arrancó") y termina con código 1.
  `estado_core(respuesta) -> bool` es pura y se prueba con respuestas simuladas.

## R7. Ajustes heredados del #7

- **(a)** `escalar_a_analista`: transacción inexistente o de otro cliente → el mismo
  `NO_ENCONTRADO` con el mismo mensaje ("No hay una transacción {id} de ese cliente."); sin
  cliente, la inexistente da ese mismo error.
- **(b)** Test de `persona_solicitada` sin cliente y con una transacción existente → éxito.
- **(c)** `CAUSAS_SIN_CLIENTE` en una línea, con el comentario arriba.
- **(d)** `specs/007-bloqueo-escalamiento/plan.md`: quitar `errores.py` del alcance.
