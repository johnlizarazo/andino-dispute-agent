---

description: "Lista de tareas del issue #11: Subagente analista-transacciones"
---

# Tasks: Subagente `analista-transacciones`

**Input**: documentos de diseño en `specs/011-subagente-analista-transacciones/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la constitución los exige en dos niveles (principio VI) y el issue pide un test que
verifique la delegación. Cada test determinista se escribe **antes** que el código, vive junto
al módulo y se ve fallar antes de implementar. El escenario `e2e` va en `tests/escenarios/`,
marcado `e2e`, con mensajes distintos de los ejemplos del prompt. Solo datos ficticios.

**Organization**: en el orden del plan: sonda con la API → US5 (heredados del #10) → US1/US4
(`analista.py`) → US1/US3 (control de delegación) → US2 (configuración) → prompt v5 →
escenario e2e → verificación y cierre. Herramienta Bash: no escribir con scripts texto que
lleve barras invertidas (se pierden); usar Write/Edit. El hook `formatear` aplica BLE001/S110:
`contextlib.suppress` o `# noqa: BLE001 - <motivo>`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US5).

---

## Phase 1: Setup - Sonda de la delegación (bloquea todo)

**Purpose**: confirmar con la API lo que el plan supone (research R1 y R3). Requiere
`ANTHROPIC_API_KEY` (nunca se lee ni imprime su valor).

- [X] T001 Escribir una sonda en el directorio de trabajo temporal (fuera del repositorio) que parta de `crear_opciones(entorno, controles)` y, sin tocar el código de producción, le agregue con `dataclasses.replace` (ajuste M1) un `AgentDefinition` mínimo de `analista-transacciones` (`tools=["mcp__core-bancario__consultar_transacciones"]`, `model="inherit"`), `tools=["Agent"]` y `"Agent"` en `allowed_tools`, y espías en `PreToolUse` (matcher `None`), `UserPromptSubmit` y `SubagentStart`; conversar como CC-FIC-0001 verificada pidiendo analizar los cobros de ayer de la 4821 con el subagente. Registrar: nombre de la herramienta de delegación y claves de su `tool_input`; si la consulta del subagente llega al `PreToolUse` con `agent_id`; si `UserPromptSubmit` se dispara durante la delegación. Anotar el resultado en esta tarea y ajustar `HERRAMIENTA_DELEGAR` y research R1/R3 si difiere. **Si la consulta del subagente no llega a los hooks, detenerse y consultar al desarrollador** (la regla 1 no quedaría garantizada). Resultado (2026-10-24): la herramienta se llama `Agent` y su entrada trae `description`, `prompt`, `subagent_type` y `run_in_background`; la consulta del subagente llega al `PreToolUse` con `agent_id` y `agent_type` `analista-transacciones` (los controles del #9 lo cubren); `UserPromptSubmit` solo se dispara con los mensajes del cliente, no con la delegación. Hallazgo: sin `background=False` el subagente corre en segundo plano y el turno termina sin su resultado; se agrega `background=False` a la definición y el control niega `run_in_background` verdadero con `SEGUNDO_PLANO_NO_PERMITIDO` (research R1, contrato y T004/T006)

---

## Phase 2: User Story 5 - Ajustes heredados del #10 (Priority: P5)

**Goal**: FR-010 ([contracts/heredados-010.md](contracts/heredados-010.md)).

**Independent Test**: `uv run pytest src/agente_disputas/test_controles.py`.

- [X] T002 [US5] (b) En `src/agente_disputas/test_controles.py`, **antes** del código: `antes_de_terminar` y `al_recibir_mensaje` con `None` y `{}` devuelven `{}` sin lanzar; `al_recibir_mensaje` con `{"agent_id": "a1", "hook_event_name": "UserPromptSubmit"}` no vacía los pendientes (research R3). Verlo fallar
- [X] T003 [US5] (c) En `src/agente_disputas/controles.py`: `al_recibir_mensaje` con `suppress(Exception)` y sin efecto si la entrada trae `agent_id`. (a) En `specs/010-escalamiento-criterio-solicitudes/tasks.md`, T006 nombra `DISPUTA_EXISTENTE` en lugar de `TRANSACCION_YA_DISPUTADA`. Dejar verde. Commit `fix(#11): ajustes heredados de las revisiones del #10`

---

## Phase 3: User Story 1 y 4 - Definición del subagente y contexto (Priority: P1, P4) 🎯 MVP

**Goal**: FR-001, FR-003, FR-007, FR-008 ([contracts/subagente.md](contracts/subagente.md)).

**Independent Test**: `uv run pytest src/agente_disputas/test_analista.py`.

- [ ] T004 [US1] Escribir `src/agente_disputas/test_analista.py`, **antes** del módulo, casos 1 a 3 del contrato: `definir_analista(politica)` con `tools == ["mcp__core-bancario__consultar_transacciones"]`, `model == "inherit"`, `maxTurns == 8`, `background is False` y `description` no vacía; `prompt_analista` con la política real contiene `$500.000`, `90`, `120`, `<contexto>`, `<analisis>`, `disputable`, `sobre_umbral` y `fuera_de_politica`; con `replace(politica, umbral_disputa_automatica=300000)` contiene `$300.000` y no `$500.000`; `leer_contexto` con un bloque válido (`cliente_id` " CLI-001 ", `ultimos4` "4821", fechas "2026-10-22", montos `[180000]`) devuelve el contexto sin espacios y `[]`; montos `[]` es válido; sin bloque → `["contexto"]`; JSON inválido → `["contexto"]`; cada campo faltante lo nombra; `ultimos4` "48A1" ("exactamente 4 dígitos"), fecha "2026-13-01" ("`AAAA-MM-DD` válida"), `fecha_desde > fecha_hasta`, montos con 0, negativo, `True`, texto o no lista ("enteros positivos") nombran el campo; un campo de más se ignora. Verlo fallar
- [ ] T005 [US1] Escribir `src/agente_disputas/analista.py` (docstring: subagente de solo consulta, contexto explícito y clasificación orientativa): `NOMBRE`, `HERRAMIENTA_DELEGAR` (según T001), `pesos(monto)` (ajuste M2: se mueve aquí desde `controles._pesos`, y `controles.py` la importa de `analista.py`, así la dependencia va en un solo sentido y no hay import circular), `prompt_analista(politica)` con `pesos`, `definir_analista(politica)` y `leer_contexto(prompt)` (extrae `<contexto>…</contexto>` con `re`, `json.loads`, valida con `date.fromisoformat` tras comprobar el patrón `AAAA-MM-DD`). Dejar verde. Commit `feat(#11): definición del subagente y lectura del contexto`

---

## Phase 4: User Story 1 y 3 - Control de la delegación (Priority: P1, P3)

**Goal**: FR-004, FR-005, FR-006.

**Independent Test**: `uv run pytest src/agente_disputas/test_controles.py -k "delega or agent_id"`.

- [ ] T006 [US3] En `src/agente_disputas/test_controles.py`, casos 4 y 5 del contrato, **antes** del código: helper `_delegar(controles, subagente, prompt)` con `tool_name` = `HERRAMIENTA_DELEGAR`; sin verificar → `SIN_IDENTIDAD`; `subagent_type` "general-purpose" → `SUBAGENTE_NO_PERMITIDO`; `run_in_background` `true` → `SEGUNDO_PLANO_NO_PERMITIDO` (ausente o `false` es válido); sin bloque o con `ultimos4` inválido → `CONTEXTO_INCOMPLETO` y la razón contiene el nombre del campo y no su valor; `cliente_id` CLI-002 con CLI-001 verificado → `CLIENTE_DISTINTO` sin "CLI-002" en la razón; delegación válida → `{}`; entrada `None`, `tool_input` no dict o sin `prompt` → negación (`FALLA_CONTROL` o `CONTEXTO_INCOMPLETO`), nunca `{}`. Consulta con `agent_id` "sub-1" sobre CLI-002 → `CLIENTE_DISTINTO`; sobre CLI-001 → `{}`. Ajuste L2: tras una delegación válida (y aunque el subagente hubiera clasificado `TRX-002` como disputable), la disputa de `TRX-002` del principal se niega con `REQUIERE_ANALISTA`. Verlo fallar
- [ ] T007 [US3] En `src/agente_disputas/controles.py`: códigos `SUBAGENTE_NO_PERMITIDO` y `CONTEXTO_INCOMPLETO` (razón con los nombres de campo, nunca valores), `antes_de_delegar` con el orden de research R2 usando `leer_contexto` y `subagent_type`, falla cerrada; `hooks()` agrega en `PreToolUse` `HookMatcher(matcher="Agent|Task", hooks=[self.antes_de_delegar], timeout=TIEMPO_MAXIMO_SEGUNDOS)`. Actualizar el docstring del módulo (delegación, #11). Dejar verde. Commit `feat(#11): control de la delegación al subagente`

---

## Phase 5: User Story 2 - Configuración: solo consulta y solo delegación (Priority: P2)

**Goal**: FR-001, FR-002.

**Independent Test**: `uv run pytest src/agente_disputas/test_configuracion.py`.

- [ ] T008 [US2] En `src/agente_disputas/test_configuracion.py`, casos 7 y 8, **antes** del código: `opciones.agents` tiene solo `analista-transacciones` con la definición de `definir_analista`; `tools == [HERRAMIENTA_DELEGAR]`; `allowed_tools` = las 6 del core con prefijo + `HERRAMIENTA_DELEGAR`; `PreToolUse` tiene el matcher de productos y el de delegación; con `Controles(lambda _: None, None)` inyectados: `agents` vacío o `None`, `tools == []` y sin la delegación en `allowed_tools`. Ajustar los tests del #8 que esperaban `tools == []` siempre. Verlo fallar
- [ ] T009 [US2] En `src/agente_disputas/configuracion.py`: registrar el subagente y la herramienta de delegación solo si `controles.politica` no es `None`; docstring actualizado. Dejar verde

---

## Phase 6: Prompt v5 (FR-009)

**Goal**: FR-009.

**Independent Test**: `uv run pytest src/agente_disputas/test_prompts.py`.

- [ ] T010 [US1] En `src/agente_disputas/test_prompts.py`, **antes** del prompt: `VERSION_PROMPT == "5"`; el prompt menciona `analista-transacciones` y `<contexto>` con los cinco campos (`cliente_id`, `ultimos4`, `fecha_desde`, `fecha_hasta`, `montos_reportados`). Los tests de ejemplos y separación del #10 siguen pasando. Verlo fallar
- [ ] T011 [US1] En `src/agente_disputas/prompts.py` (con Write/Edit, no scripts): sección "Análisis con analista-transacciones" según research R5 (cuándo delegar, formato exacto del bloque, usar la clasificación, los controles deciden, no delegar sin verificación ni para otro cliente); `VERSION_PROMPT = "5"`; líneas ≤ 95 caracteres; sin datos del core dentro de `<ejemplos>`. Dejar verde. Commit `feat(#11): subagente registrado y prompt v5`

---

## Phase 7: Escenario de delegación (FR-005, test del issue)

- [ ] T012 [US3] Escribir `tests/escenarios/test_delegacion_e2e.py` (marcado `e2e`, se salta sin la clave) según el contrato: `Controles.desde_entorno`, espías que envuelven `antes_de_herramienta` y `antes_de_delegar` registrando `tool_name` y `agent_id`; mensaje distinto de los ejemplos del prompt (clienta CC-FIC-0001 con su dato de verificación, leído del repositorio en tiempo de ejecución, que pide revisar los cobros de ayer de su tarjeta antes de reclamar); aserciones: una delegación autorizada a `analista-transacciones`, al menos una `consultar_transacciones` con `agent_id` llegó a los controles, y ninguna `iniciar_disputa` de `TRX-002` fue autorizada. Comprobar que se salta sin la clave. Commit `test(#11): escenario de delegación`

---

## Phase 8: Verificación

- [ ] T013 Ejecutar `uv run pytest` completo, `ruff check src tests` y `ruff format --check src tests` en verde ([quickstart.md §1](quickstart.md))
- [ ] T014 Ejecutar `uv run pytest -m e2e -s` ([quickstart.md §3](quickstart.md)); si el motor se cierra abruptamente (visto en el #10), repetir y anotarlo
- [ ] T015 Conversación de [quickstart.md §4](quickstart.md) (a–c) con una sonda que registre herramientas, `agent_id` y el bloque `<analisis>`; ajuste L1: en el caso (a), el cliente reporta además un monto que no existe y se comprueba que aparece en `montos_no_encontrados`; anotar el resultado de cada caso en esta tarea
- [ ] T016 Pasar `bloquear_pii.py --diff` sobre un archivo con `git diff --unified=0 main...HEAD` sin hallazgos

---

## Phase 9: Cierre con `/abrir-pr`

- [ ] T017 Verificar `uv run pytest` en verde y el árbol limpio
- [ ] T018 Marcar T001 a T018 en `specs/011-subagente-analista-transacciones/tasks.md` y hacer commit. T019 y T020 se marcan en la rama del issue siguiente
- [ ] T019 El desarrollador ejecuta `/abrir-pr` y aprueba el push y el PR. Esperado: revisión de código `APROBADO`, cumplimiento `APROBADO`, PR con `Closes #11`, CI `guardrails` en verde, issue en *In Review* y comentario de avance
- [ ] T020 Después del merge, hecho por el desarrollador: verificar que el #11 queda cerrado y en *Done*

---

## Dependencies & Execution Order

- **Sonda (T001)**: primero; puede cambiar `HERRAMIENTA_DELEGAR` o detener el ticket.
- **US5 (T002–T003)**: tras T001; independiente del resto.
- **US1/US4 (T004–T005)**: tras T001 (`HERRAMIENTA_DELEGAR`).
- **US1/US3 (T006–T007)**: tras T005 (`leer_contexto`) y T003 (mismo archivo).
- **US2 (T008–T009)**: tras T005 y T007.
- **Prompt (T010–T011)**: tras T005 (nombres y formato).
- **Escenario (T012)**: tras T009 y T011.
- **Verificación (T013–T016)** y **cierre (T017–T020)**: al final.

### Parallel Opportunities

- T002–T003 con T004–T005 (archivos distintos); T010 con T008.

## Parallel Example: User Story 1

```text
Task: "T004 Tests de la definición y el contexto en src/agente_disputas/test_analista.py"
Task: "T002 Tests heredados en src/agente_disputas/test_controles.py"
```

## Implementation Strategy

### MVP

Sonda + definición del subagente + control de la delegación: el subagente existe, solo
consulta y no se le puede delegar sin cliente verificado y contexto completo.

### Incremental Delivery

Un commit por fase con el test escrito antes. El subagente se habilita en la configuración
(T009) cuando el control de delegación ya está en verde.
