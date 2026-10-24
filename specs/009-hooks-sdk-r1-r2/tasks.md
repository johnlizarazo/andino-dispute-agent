---

description: "Lista de tareas del issue #9: Hooks del SDK para R1 y R2"
---

# Tasks: Hooks del SDK para R1 y R2

**Input**: documentos de diseño en `specs/009-hooks-sdk-r1-r2/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la constitución los exige en dos niveles (principio VI) y el issue pide tests
unitarios de los hooks sin API y un test sin prompt. Cada test determinista se escribe
**antes** que el código, vive junto al módulo y se ve fallar antes de implementar. Los
callbacks se prueban llamándolos con `asyncio.run` y diccionarios de entrada construidos a
mano (`tool_name`, `tool_input`, `tool_response`). Los escenarios `e2e` van en
`tests/escenarios/`, se marcan `e2e`, se saltan sin `ANTHROPIC_API_KEY` y sus mensajes
difieren de los ejemplos del prompt. Solo datos ficticios (`CLI-00N`, `TRX-00N`).

**Organization**: en el orden del plan: US5 (heredados del #8) → controles (US1, US2, US3) →
configuración y prompt (US4) → escenario e2e → verificación y cierre. El hook `formatear`
elimina imports sin uso entre ediciones: agregar el import en la misma edición que su uso.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US5).

---

## Phase 1: User Story 5 - Ajustes heredados de las revisiones del #8 (Priority: P5, primero por el plan)

**Goal**: FR-011 ([contracts/heredados-008.md](contracts/heredados-008.md)).

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_bloqueo_escalamiento.py src/agente_disputas/test_cli.py`.

- [X] T001 [US5] (a) En `src/core_bancario_mcp/test_bloqueo_escalamiento.py`, **antes** de tocar el módulo: reemplazar `test_persona_solicitada_sin_cliente_acepta_transacciones` por `test_persona_solicitada_sin_cliente_rechaza_transacciones`: sin `cliente_id`, `["TRX-001"]` y `["TRX-999"]` responden `validacion` / `PARAMETRO_INVALIDO` con respuestas **idénticas**; verlo fallar
- [X] T002 [US5] (a) En `src/core_bancario_mcp/bloqueo_escalamiento.py`, después de validar `cliente_id`: si no hay cliente y `ids` no está vacío → `_invalido("sin cliente_id no se indican transacciones")`, antes de consultar el repositorio. Ajustar la descripción de la herramienta (sin cliente, solo causa y resumen) y `.claude/rules/herramientas-mcp.md` (escalar sin cliente no lleva transacciones). Dejar verdes los tests del core
- [X] T003 [P] [US5] (b) En `src/agente_disputas/test_cli.py`: dos tests de `main()` con `validar_credencial` satisfecha (entorno con clave ficticia vía `monkeypatch.setenv`) y `cli._ejecutar` reemplazado por una corrutina que lanza `KeyboardInterrupt` → devuelve 0 e imprime la despedida; y `CLINotFoundError` → devuelve 1, mensaje en stderr, sin traza (`capsys`)
- [X] T004 [P] [US5] (c), (d) y (e): texto de T007 en `specs/008-ciclo-agentico-mcp/tasks.md` alineado con lo implementado en el #8 (`allowed_tools` = 3 exentas, `disallowed_tools` = 3 sobre productos); `procesar_turno(mensajes: AsyncIterable[Message])` en `src/agente_disputas/ciclo.py` (importar `Message` de `claude_agent_sdk`); líneas de `src/agente_disputas/cli.py` de más de 95 caracteres partidas. Commit `fix(#9): ajustes heredados de las revisiones del #8`

---

## Phase 2: Foundational - Estado y registro de la verificación (bloquea US1 a US3)

**Goal**: FR-001, FR-002 ([data-model.md](data-model.md), research R3 y R4).

- [X] T005 Escribir en `src/agente_disputas/test_controles.py`, **antes** del módulo, los casos 3, 4 y 7 de [contracts/controles.md](contracts/controles.md): `leer_respuesta` con cada forma aceptada (dict con `ok`; dict con `structuredContent`; dict con `content` de bloques; lista de bloques `{"type": "text", "text": "<json>"}`; texto JSON) y rechazadas (`None`, `"x"`, `[]`, `42`, JSON sin `ok`); `despues_de_verificar` registra CLI-001 solo con `{"ok": true, "datos": {"verificado": true, "cliente_id": "CLI-001"}}` y `tool_input` `{"cliente_id": " CLI-001 "}`; no registra con `ok: false`, respuesta ilegible o `cliente_id` de la respuesta distinto del pedido; una segunda verificación exitosa de CLI-002 reemplaza; un fallo posterior no borra al anterior; devuelve siempre `{}` y nunca lanza (también con `input` sin claves). Verlo fallar
- [X] T006 Escribir `src/agente_disputas/controles.py` (docstring: garantía de las reglas 1 y 2 por hook, falla cerrada): `Negacion` (`herramienta`, `codigo`), `EstadoSesion` (`cliente_verificado: str | None = None`, `negaciones: list[Negacion]`), `leer_respuesta(tool_response) -> dict | None`, y la clase `Controles(estado, buscar_transaccion, politica)` con `despues_de_verificar`. Dejar verdes los tests de T005

---

## Phase 3: User Story 1 - Sin identidad verificada no se opera sobre productos (Priority: P1) 🎯 MVP

**Goal**: FR-003, FR-005; caso de prueba del issue.

**Independent Test**: `uv run pytest src/agente_disputas/test_controles.py -k identidad`.

- [X] T007 [US1] En `src/agente_disputas/test_controles.py`, caso 1: sin verificar, `antes_de_herramienta` niega `consultar_transacciones` (`cliente_id` CLI-001, `ultimos4` 4821), `iniciar_disputa` (`TRX-001`) y `bloquear_tarjeta` con `permissionDecision` `"deny"`, `hookEventName` `"PreToolUse"`, una razón que menciona verificar la identidad y una `Negacion` `SIN_IDENTIDAD` por cada una; tras verificar CLI-001 las tres se autorizan (`{}`); un `tool_name` fuera de las tres (p. ej. `mcp__core-bancario__otra`) se niega con `FALLA_CONTROL`. Verlo fallar
- [X] T008 [US1] En `src/agente_disputas/controles.py`: `Decision` (`autorizada`, `codigo`, `razon`), constantes con los nombres completos de las 3 herramientas, `antes_de_herramienta` que despacha por `tool_name`, comprueba identidad primero y traduce la `Decision` a la salida del hook (negar agrega la `Negacion`). Razones en español según la tabla del contrato. Dejar verde

---

## Phase 4: User Story 2 - Solo sobre productos del cliente verificado (Priority: P2)

**Goal**: FR-004.

**Independent Test**: `uv run pytest src/agente_disputas/test_controles.py -k titular`.

- [X] T009 [US2] En `src/agente_disputas/test_controles.py`, casos 2, 5 (titularidad) y 8: con CLI-001 verificado, consultar/bloquear con `cliente_id` CLI-002, ausente, `None`, `123` o `["CLI-001"]` → `CLIENTE_DISTINTO`, y la razón no contiene "CLI-002"; con `" CLI-001 "` autoriza; disputar `TRX-004` (de CLI-002) y `TRX-999` → `TRANSACCION_NO_CONFIRMADA` con **la misma** razón; `transaccion_id` ausente o no texto → la misma; `" TRX-001 "` autoriza; tras verificar CLI-002, `TRX-004` autoriza y `TRX-001` se niega. Los tests usan el `Repositorio()` real de datos ficticios. Verlo fallar
- [X] T010 [US2] En `src/agente_disputas/controles.py`: titularidad por `cliente_id` (texto, sin espacios) para consultar y bloquear, y por `buscar_transaccion(id).cliente_id` para disputar. Dejar verde

---

## Phase 5: User Story 3 - Disputas sobre el umbral se niegan antes del core (Priority: P3)

**Goal**: FR-006, FR-007.

**Independent Test**: `uv run pytest src/agente_disputas/test_controles.py -k "umbral or falla"`.

- [X] T011 [US3] En `src/agente_disputas/test_controles.py`, casos 5 (umbral) y 6: con CLI-001 verificado, `TRX-002` (1250000) → `REQUIERE_ANALISTA` con razón que menciona un analista; `TRX-001` (180000) autoriza; con CLI-002, `TRX-004` (exactamente 500000) autoriza. Falla cerrada → `FALLA_CONTROL` en todos: `Controles.desde_entorno({"CORE_BANCARIO_FALLAS": "control_transaccion:1"})` niega la primera disputa y autoriza la segunda; repositorio que no carga (`Repositorio` reemplazado con `monkeypatch` por uno que lanza `DatosInvalidosError`); `buscar_transaccion` que lanza `RuntimeError`; `politica` `None`; `tool_input` que no es dict; `CORE_BANCARIO_FALLAS` inválida. Ningún caso autoriza. Verlo fallar
- [X] T012 [US3] En `src/agente_disputas/controles.py`: umbral con `politica.requiere_analista(transaccion.monto)` después de la titularidad; `try/except Exception` envolviendo toda la lógica de `antes_de_herramienta` (y de `despues_de_verificar`) con negación `FALLA_CONTROL`; `Controles.desde_entorno(entorno)` que carga `Repositorio()` e `InyectorFallas(entorno.get("CORE_BANCARIO_FALLAS"))` y envuelve la consulta con la operación `control_transaccion` (si falla la carga o la configuración, controles sin datos); `hooks()` que devuelve los dos `HookMatcher` del contrato con `timeout=10`. Dejar verde. Commit `feat(#9): controles de identidad, titularidad y umbral`

---

## Phase 6: User Story 4 - Las garantías no dependen del prompt (Priority: P4)

**Goal**: FR-008, FR-009, FR-010.

**Independent Test**: `uv run pytest src/agente_disputas/test_configuracion.py src/agente_disputas/test_prompts.py`.

- [X] T013 [P] [US4] En `src/agente_disputas/test_configuracion.py`, casos 9 a 12: `opciones.hooks["PreToolUse"]` tiene un matcher exactamente `"mcp__core-bancario__consultar_transacciones|mcp__core-bancario__iniciar_disputa|mcp__core-bancario__bloquear_tarjeta"` y `opciones.hooks["PostToolUse"]` uno exactamente `"mcp__core-bancario__verificar_identidad"`; ningún matcher menciona `buscar_cliente` ni `escalar_a_analista`; `allowed_tools` son las 6 con prefijo y `disallowed_tools == []`; con `dataclasses.replace(opciones, system_prompt=None)`, el callback del `PreToolUse` registrado niega `iniciar_disputa` `TRX-001` sin verificación; dos `crear_opciones` tienen estados distintos; `crear_opciones(entorno, controles=c)` usa ese `c`. Reemplazar los tests del #8 que esperaban 3 deshabilitadas. Verlo fallar
- [X] T014 [P] [US4] En `src/agente_disputas/test_prompts.py`: `VERSION_PROMPT == "3"`, `"Disponibilidad actual"` no está en el prompt y ninguna línea del archivo `prompts.py` supera 95 caracteres. Verlo fallar
- [X] T015 [US4] En `src/agente_disputas/configuracion.py`: `crear_opciones(entorno, controles: Controles | None = None)`, `hooks=controles.hooks()`, las 6 en `allowed_tools`, `disallowed_tools=[]`; eliminar `HERRAMIENTAS_HABILITADAS` y actualizar el docstring (reglas 1 y 2 por hook desde el #9). Dejar verde T013
- [X] T016 [US4] En `src/agente_disputas/prompts.py`: quitar "Disponibilidad actual", agregar "Cuando una operación se niega" (explicar sin detalles internos; si pide verificar, verificar; si pide analista, escalar con la causa que corresponda; no reintentar la misma operación negada). Ajuste L1: la sección cubre las dos vías por las que llega una negación, el error del core (`REQUIERE_ANALISTA`, `FUERA_DE_POLITICA`) y la negación previa de un control, y en `escalar_a_analista` se menciona también la negación por umbral de un control; `VERSION_PROMPT = "3"`, líneas ≤ 95 caracteres, y docstring que nombra los hooks del #9. Dejar verde T014. Commit `feat(#9): hooks en las opciones, 6 herramientas y prompt v3`
- [ ] T017 [US4] En `tests/escenarios/test_conversacion_e2e.py`: escenario sin prompt de sistema (`replace(crear_opciones(entorno, controles=c), system_prompt=None)`) con un mensaje que pide disputar directamente un cobro (`TRX-002`) sin identificarse, distinto de los ejemplos del prompt; aserción (ajuste M1): ninguna llamada a `iniciar_disputa` llegó al core, es decir, la cantidad de `mcp__core-bancario__iniciar_disputa` en `resultado.herramientas` es igual a la cantidad de `Negacion` de esa herramienta en `c.estado.negaciones` (cero y cero vale), y todas tienen código `SIN_IDENTIDAD`. Comprobar que se salta sin la clave (`uv run pytest -m e2e` sin la variable)

---

## Phase 7: Verificación

**Purpose**: requiere `ANTHROPIC_API_KEY` en el entorno (nunca se lee ni imprime su valor).

- [ ] T018 Ejecutar `uv run pytest` completo y `uv run --no-sync ruff check src tests` y `ruff format --check` en verde ([quickstart.md §1](quickstart.md))
- [ ] T019 Ejecutar `uv run pytest -m e2e -s` ([quickstart.md §2](quickstart.md))
- [ ] T020 Conversación de [quickstart.md §3](quickstart.md) (a–e). En (b), confirmar que el control registró al cliente (la disputa se autoriza); si no, registrar la forma real de `tool_response` (sin datos fuera de los ficticios) y ajustar `leer_respuesta` con su test antes de seguir
- [ ] T021 Pasar `bloquear_pii.py --diff` sobre un archivo con `git diff --unified=0 main...HEAD` sin hallazgos

---

## Phase 8: Cierre con `/abrir-pr`

- [ ] T022 Verificar `uv run pytest` en verde y el árbol limpio
- [ ] T023 Marcar T001 a T023 en `specs/009-hooks-sdk-r1-r2/tasks.md` y hacer commit. T024 y T025 se marcan en la rama del issue siguiente
- [ ] T024 El desarrollador ejecuta `/abrir-pr` y aprueba el push y el PR. Esperado: revisión de código `APROBADO`, cumplimiento `APROBADO`, PR con `Closes #9`, CI `guardrails` en verde, issue en *In Review* y comentario de avance
- [ ] T025 Después del merge, hecho por el desarrollador: verificar que el #9 queda cerrado y en *Done*

---

## Dependencies & Execution Order

- **US5 (T001–T004)**: primero; independiente de los controles. T003 y T004 en paralelo con
  T001–T002.
- **Foundational (T005–T006)**: bloquea US1 a US3 (estado y registro de la verificación).
- **US1 → US2 → US3 (T007–T012)**: secuenciales en el mismo archivo; cada una extiende
  `antes_de_herramienta` en el orden identidad → titularidad → umbral.
- **US4 (T013–T017)**: después de T012 (`Controles.desde_entorno` y `hooks()`). T013 y T014 en
  paralelo; T015 antes de T017.
- **Verificación (T018–T021)** y **cierre (T022–T025)**: al final.

### Parallel Opportunities

- T003 y T004 con T001–T002; T013 con T014.

## Parallel Example: User Story 4

```text
Task: "T013 Tests de hooks y herramientas en src/agente_disputas/test_configuracion.py"
Task: "T014 Tests del prompt v3 en src/agente_disputas/test_prompts.py"
```

## Implementation Strategy

### MVP

Foundational + US1: sin identidad verificada no se opera (el caso de prueba del issue). Las
herramientas siguen deshabilitadas hasta US4, así que cada incremento es seguro.

### Incremental Delivery

Un commit por fase con el test escrito antes. Las 3 herramientas sobre productos se habilitan
solo en T015, cuando los controles de identidad, titularidad y umbral ya están en verde.
