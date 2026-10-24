---

description: "Lista de tareas del issue #8: Ciclo agéntico y conexión al MCP"
---

# Tasks: Ciclo agéntico y conexión al MCP

**Input**: documentos de diseño en `specs/008-ciclo-agentico-mcp/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la constitución los exige en dos niveles (principio VI). Cada test determinista se
escribe **antes** que el código, vive junto al módulo (rule `tests.md`) y se ve fallar antes de
implementar; no llama a la API. Los escenarios `e2e` van en `tests/escenarios/`, se marcan
`@pytest.mark.e2e`, se saltan sin `ANTHROPIC_API_KEY` y sus mensajes difieren de los ejemplos
del prompt. Ningún test, mensaje ni registro contiene el valor de la clave.

**Organization**: en el orden del plan: US5 (heredados del #7) → configuración (US3) → ciclo
(US2) → CLI (US1 y US4) → escenario e2e (US4), luego verificación y cierre. El hook
`formatear` elimina imports sin uso entre ediciones: agregar el import en la misma edición que
su uso.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US5).

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Crear la carpeta `tests/escenarios/` con un `__init__.py` vacío solo si pytest lo necesita para recolectar (comprobar con `uv run pytest --collect-only -q tests` tras crear el primer test)

---

## Phase 2: User Story 5 - Ajustes heredados de la revisión del #7 (Priority: P5, primero por el plan)

**Goal**: FR-014 ([contracts/heredados-007.md](contracts/heredados-007.md)).

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_bloqueo_escalamiento.py`.

- [X] T002 [US5] (a) y (b) En `src/core_bancario_mcp/test_bloqueo_escalamiento.py`, **antes** de tocar el módulo: cambiar `test_transaccion_inexistente_ajena_o_cliente_inexistente` para que `TRX-999` y `TRX-004` con CLI-001 den respuestas **idénticas** (`NO_ENCONTRADO`, mismo mensaje), y agregar un test de `persona_solicitada` sin cliente y con `["TRX-001"]` → éxito con `cantidad_transacciones` 1; ver fallar el primero
- [X] T003 [US5] (a) y (c) En `src/core_bancario_mcp/bloqueo_escalamiento.py`: un solo `NO_ENCONTRADO` con el mensaje, sin el id para que las respuestas sean idénticas, "Una de las transacciones indicadas no corresponde a ese cliente." para transacción inexistente o de otro cliente (sin cliente, la inexistente da ese mismo error); `CAUSAS_SIN_CLIENTE` en una sola línea con su comentario en la línea de arriba. Dejar verdes los tests
- [X] T004 [P] [US5] (d) En `specs/007-bloqueo-escalamiento/plan.md`, quitar `errores.py` del alcance (Scale/Scope y estructura). Commit `fix(#8): ajustes heredados de la revisión del #7`

---

## Phase 3: User Story 3 - El agente solo puede usar el core bancario (Priority: P3, base del resto)

**Goal**: FR-007 a FR-010b ([contracts/configuracion.md](contracts/configuracion.md)).

**Independent Test**: `uv run pytest src/agente_disputas/test_prompts.py src/agente_disputas/test_configuracion.py`.

- [X] T005 [P] [US3] Escribir `src/agente_disputas/test_prompts.py` **antes** del módulo: `PROMPT_SISTEMA` menciona las 6 herramientas, "$500.000", "reintentable" y "dos veces"; `VERSION_PROMPT` no está vacío; verlo fallar
- [X] T006 [US3] Escribir `src/agente_disputas/prompts.py` con `VERSION_PROMPT = "1"` y `PROMPT_SISTEMA` según [contracts/configuracion.md](contracts/configuracion.md): rol, español, las 5 reglas de la constitución, cuándo usar cada herramienta, no inventar datos ni montos, y manejo de errores ("reintentable: true" → reintentar la misma llamada hasta dos veces y luego informar sin detalles técnicos y ofrecer escalar; "reintentable: false" → no repetir y actuar según tipo). Sin datos de clientes reales; los ejemplos usan solo datos ficticios. Dejar verde el test
- [X] T007 [P] [US3] Escribir `src/agente_disputas/test_configuracion.py` **antes** del módulo, sin API, con un `entorno` de prueba (diccionario) que contiene una clave ficticia `"clave-de-prueba"` (nunca una real), y verlo fallar:
  - `tools == []`, `permission_mode == "dontAsk"`, `strict_mcp_config is True`, `setting_sources == []`, `max_turns == 25`.
  - `HERRAMIENTAS` son las 6 del core; `allowed_tools` es exactamente las 3 exentas de identidad (`buscar_cliente`, `verificar_identidad`, `escalar_a_analista`) con el prefijo `mcp__core-bancario__`, y `disallowed_tools` las otras 3 (ajuste T023; el #9 las habilita junto con sus hooks).
  - `mcp_servers` tiene solo `core-bancario`: `type` `"stdio"`, `command` `sys.executable`, `args` `["-m", "core_bancario_mcp"]`.
  - Sin `CORE_BANCARIO_FALLAS` en el entorno, el `env` del servidor no la tiene; con ella, la pasa tal cual.
  - `model` es `"claude-sonnet-5-5"` por omisión y `ANDINO_MODELO` lo cambia.
  - `system_prompt` es `PROMPT_SISTEMA`.
  - `validar_credencial` lanza `CredencialFaltanteError` sin `ANTHROPIC_API_KEY` y con `"   "`; el mensaje contiene "ANTHROPIC_API_KEY" y no contiene "clave-de-prueba".
- [X] T008 [US3] Implementar `src/agente_disputas/configuracion.py` según [research.md R3 y R4](research.md): `HERRAMIENTAS`, `MODELO_POR_OMISION`, `MAXIMO_PASOS_POR_TURNO = 25` con un comentario que lo declare salvaguarda (FR-006), `CredencialFaltanteError`, `validar_credencial(entorno)` y `crear_opciones(entorno)` (recibe el entorno como `Mapping` para que los tests no toquen `os.environ`). La clave no se copia a las opciones: el SDK la hereda del entorno. Dejar verdes los tests y hacer commit `feat(#8): prompt y configuración del agente limitada al core bancario`

---

## Phase 4: User Story 2 - El ciclo sigue o termina según la razón de parada (Priority: P2)

**Goal**: FR-004 a FR-006 ([contracts/ciclo-y-cli.md](contracts/ciclo-y-cli.md)).

**Independent Test**: `uv run pytest src/agente_disputas/test_ciclo.py`.

- [X] T009 [US2] Escribir `src/agente_disputas/test_ciclo.py` **antes** del módulo, con mensajes construidos con las clases reales de `claude_agent_sdk` (`AssistantMessage`, `UserMessage`, `ResultMessage`, `TextBlock`, `ToolUseBlock`, `ToolResultBlock`) entregados por un generador asíncrono, y verlo fallar:
  - `tool_use` + resultado + `end_turn` con texto + `ResultMessage(subtype="success")` → `ResultadoTurno(estado="completado")`, el texto final y `herramientas == ("mcp__core-bancario__buscar_cliente",)`.
  - `subtype="error_max_turns"` → `salvaguarda`; `terminal_reason="max_turns"` → `salvaguarda`.
  - `is_error=True, api_error_status=529` → `falla_servicio`; otro error → `error`; flujo sin `ResultMessage` → `error`.
  - Un texto del modelo con "listo", "fin" o "terminé" antes de un `tool_use` no cierra el turno (no hay búsqueda de palabras).
  - `estado_core` es verdadero solo con `core-bancario` en estado `connected` (respuestas simuladas con la forma de `get_mcp_status`).
- [X] T010 [US2] Implementar `src/agente_disputas/ciclo.py`: `ResultadoTurno` (dataclass inmutable con "`estado`: `completado`, `salvaguarda`, `falla_servicio`, `error`", `texto`, `herramientas`, `detalle`), `clasificar(resultado)`, `procesar_turno(mensajes)` y `estado_core(respuesta)` según [research.md R2 y R6](research.md); sin contadores ni búsqueda de palabras. Dejar verdes los tests y hacer commit `feat(#8): ciclo del turno según la razón de parada`

---

## Phase 5: User Story 1 y 4 - Conversar turno a turno y manejar errores (Priority: P1 y P4)

**Goal**: FR-001 a FR-003 y FR-011 a FR-013 ([contracts/ciclo-y-cli.md](contracts/ciclo-y-cli.md)).

**Independent Test**: `uv run pytest src/agente_disputas/test_cli.py`.

- [X] T011 [US1] Escribir `src/agente_disputas/test_cli.py` **antes** del módulo, con un cliente falso (métodos `query` y `receive_response` que entregan mensajes preparados del SDK) y entrada/salida en memoria, y verlo fallar:
  - Dos mensajes → dos respuestas en orden; la línea vacía no se envía al cliente.
  - `/salir` y el fin de entrada terminan con código 0.
  - Los estados `salvaguarda`, `falla_servicio` y `error` muestran sus avisos (sin `api_error_status`, códigos ni trazas) y el bucle sigue esperando.
  - `main` sin `ANTHROPIC_API_KEY` (entorno parchado) devuelve 1 y el mensaje nombra la variable sin trazas.
  - Una entrada simulada que lanza `KeyboardInterrupt` (Ctrl+C) hace que `conversar` termine con código 0 y una despedida, sin traza (ajuste L2).
- [X] T012 [US1] Implementar `src/agente_disputas/cli.py` (`conversar(cliente, entrada, salida) -> int` y `main() -> int`) y `src/agente_disputas/__main__.py` según [contracts/ciclo-y-cli.md](contracts/ciclo-y-cli.md): validar la credencial; crear opciones; conectar con `ClaudeSDKClient`; comprobar el core con `estado_core` (no conectado → "el core bancario no arrancó" y 1); conversar; capturar `CLINotFoundError`, `CLIConnectionError` y `ProcessError` con mensaje claro y 1; Ctrl+C → despedida y 0; desconectar siempre. Dejar verdes los tests y hacer commit `feat(#8): línea de comandos para conversar con el agente`
- [X] T013 [US4] Escribir `tests/escenarios/test_conversacion_e2e.py` (marcado `e2e`, `pytest.skip` si falta `ANTHROPIC_API_KEY`): con `CORE_BANCARIO_FALLAS="buscar_cliente:1"`, un mensaje del cliente que da un documento ficticio (distinto de los ejemplos del prompt) → `ResultadoTurno.estado == "completado"`, `mcp__core-bancario__buscar_cliente` aparece al menos dos veces en `herramientas` y el texto no contiene `FALLA_TRANSITORIA`. Agregar un segundo escenario (ajuste M1): con `CORE_BANCARIO_FALLAS="buscar_cliente:5"` (falla persistente), el turno termina `completado`, `mcp__core-bancario__buscar_cliente` aparece **como máximo 3 veces** (la llamada y dos reintentos), el texto ofrece escalar o hablar con una persona y no contiene `FALLA_TRANSITORIA`. Ambos escenarios registran con `print` el tiempo hasta el resultado como dato, sin fallar por él (ajuste L1). Confirmar con `uv run pytest` que se excluyen por omisión. Commit `test(#8): escenarios e2e de falla transitoria y persistente`

---

## Phase 6: Verificación

**Purpose**: requiere `ANTHROPIC_API_KEY` en el entorno (el desarrollador la define; nunca se
lee su valor) y una sesión que la vea.

- [X] T014 Ejecutar `uv run pytest` completo y `uv run --no-sync ruff check src tests` en verde ([quickstart.md §1](quickstart.md))
- [X] T015 Ejecutar `uv run pytest -m e2e -s` ([quickstart.md §2](quickstart.md)) y la conversación de [quickstart.md §3](quickstart.md) (4 pasos y las dos variantes de arranque fallido), anotando el tiempo de la primera respuesta frente al objetivo de SC-005 (menos de 30 s; ajuste L1)
- [ ] T016 *(Opcional, si hay una máquina o contenedor Linux disponible)* Ejecutar [quickstart.md §3b](quickstart.md); si no hay entorno, anotarlo en el comentario de avance del PR y no bloquear el cierre
- [X] T017 Pasar `bloquear_pii.py --diff` sobre un archivo con `git diff --unified=0 main...HEAD` sin hallazgos ([quickstart.md §4](quickstart.md))

---

## Phase 7: Cierre con `/abrir-pr`

- [X] T018 Verificar `uv run pytest` en verde y el árbol limpio
- [X] T019 Marcar T001 a T019 en `specs/008-ciclo-agentico-mcp/tasks.md` (T016 marcada solo si se hizo) y hacer commit. T020 y T021 ocurren después del último commit y se marcan en la rama del issue siguiente
- [X] T020 El desarrollador ejecuta `/abrir-pr` y aprueba el push y el PR. Esperado: revisión de código `APROBADO`, cumplimiento `APROBADO`, PR con `Closes #8`, CI `guardrails` en verde, issue en *In Review* y comentario de avance
- [X] T021 Después del merge, hecho por el desarrollador: verificar que el #8 queda cerrado y en *Done*

---

## Phase 8: Ajustes de las revisiones del PR

**Purpose**: correcciones pedidas por `revisor-codigo` (bloqueante y no bloqueantes) y por
`revisar-cumplimiento` (bloqueante de la regla 1, opción A aprobada por el desarrollador).

- [X] T022 Alinear el contrato con la firma real de `clasificar` (`(estado, detalle)`) y con los nombres de `conversar` (`leer`, `escribir`); test de credencial con `pytest.raises` y `"   "`; tests de la espera del core y del arranque con el core no conectado; texto de T003 alineado con el mensaje unificado
- [X] T023 Regla 1 por diseño hasta el #9: en `src/agente_disputas/configuracion.py`, `HERRAMIENTAS_HABILITADAS` con las 3 exentas en `allowed_tools` y las 3 sobre productos en `disallowed_tools`; tests en `src/agente_disputas/test_configuracion.py`; prompt (versión 2) con la disponibilidad actual en `src/agente_disputas/prompts.py`
- [X] T024 En `src/agente_disputas/ciclo.py`, solo 429 y 5xx son `falla_servicio`; 400, 401 y 403 son `error` (tests en `test_ciclo.py`). En `src/agente_disputas/cli.py`, cualquier `ClaudeSDKError` al arrancar termina sin traza (test en `test_cli.py`)
- [X] T025 Actualizar spec (FR-008, SC-002, US3, supuestos), plan, research, data-model, contrato y quickstart
- [X] T026 Volver a ejecutar las dos revisiones de `/abrir-pr` y, si aprueban, continuar con T020

---

## Dependencies & Execution Order

- **Setup (T001)** y **US5 (T002–T004)**: primero; independientes del agente.
- **US3 (T005–T008)**: base de todo lo demás. T005 y T007 en paralelo; T006 antes de T008
  (la configuración usa el prompt).
- **US2 (T009–T010)**: independiente de US3 (solo usa tipos del SDK); puede ir en paralelo.
- **US1/US4 (T011–T013)**: después de US2 y US3.
- **Verificación (T014–T017)**: requiere la credencial en la sesión.
- **Cierre (T018–T021)**: requiere la verificación (salvo T016, opcional).

### Parallel Opportunities

- T004 con T002/T003; T005 con T007; US2 (T009–T010) con US3.

## Parallel Example: User Story 3

```text
Task: "T005 Tests del prompt en src/agente_disputas/test_prompts.py"
Task: "T007 Tests de la configuración en src/agente_disputas/test_configuracion.py"
```

## Implementation Strategy

### MVP

US3 + US2 + US1: configuración segura, ciclo correcto y conversación en la terminal.

### Incremental Delivery

Un commit por paso con el test escrito antes. El escenario e2e y la verificación necesitan la
credencial; los tests deterministas no.
