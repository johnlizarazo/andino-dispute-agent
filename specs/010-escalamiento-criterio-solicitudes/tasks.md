---

description: "Lista de tareas del issue #10: Escalamiento con criterio y solicitudes múltiples"
---

# Tasks: Escalamiento con criterio y solicitudes múltiples

**Input**: documentos de diseño en `specs/010-escalamiento-criterio-solicitudes/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la constitución los exige en dos niveles (principio VI) y el issue pide tests del
escalamiento pendiente y del mensaje de ejemplo. Cada test determinista se escribe **antes**
que el código, vive junto al módulo y se ve fallar antes de implementar. Los callbacks se
prueban con `asyncio.run` y diccionarios de entrada construidos a mano. Los escenarios
automáticos del #10 son del #13; aquí la validación con la API es manual (quickstart §3). Solo
datos ficticios.

**Organization**: en el orden del plan: US6 (heredados del #9) → estado (base) → US1 y US2
(pendientes, `Stop`, aviso) → US3 a US5 (descripción y prompt v4) → verificación y cierre. El
hook `formatear` elimina imports sin uso entre ediciones y aplica BLE001/S110: agregar el
import en la misma edición que su uso y usar `# noqa: BLE001 - <motivo>` en las capturas
amplias justificadas.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US6).

---

## Phase 1: User Story 6 - Ajustes heredados del #9 (Priority: P6, primero por el plan)

**Goal**: FR-012 ([contracts/heredados-009.md](contracts/heredados-009.md)).

**Independent Test**: `uv run pytest src/agente_disputas`.

- [ ] T001 [US6] (a) y (b) En `src/agente_disputas/test_controles.py`, **antes** del código: `test_entrada_mal_formada_niega` comprueba además que la negación se registra con herramienta `"desconocida"`; nuevo test: con `Controles(repositorio.obtener_transaccion, replace(repositorio.politica, umbral_disputa_automatica=300000))`, CLI-001 verificado y `TRX-002`, la razón contiene `"$300.000"` y no `"$500.000"`. Verlos fallar
- [ ] T002 [US6] (a), (b) y (c) En `src/agente_disputas/controles.py`: constante `HERRAMIENTA_DESCONOCIDA = "desconocida"` usada cuando `tool_name` no es texto; la razón de `REQUIERE_ANALISTA` se arma con `self.politica.umbral_disputa_automatica` formateado con punto de miles (`f"{umbral:,}".replace(",", ".")`), y el resto de razones sigue en `RAZONES`; un solo `return {}` en `despues_de_verificar`. Dejar verde
- [ ] T003 [P] [US6] (d) y (e): `if controles is None:` en `src/agente_disputas/configuracion.py`; docstring de `src/agente_disputas/__init__.py` partido en líneas ≤ 95 caracteres. Commit `fix(#10): ajustes heredados de las revisiones del #9`

---

## Phase 2: Foundational - Estado de pendientes (bloquea US1 y US2)

**Goal**: entidades de [data-model.md](data-model.md).

- [ ] T004 Escribir en `src/agente_disputas/test_controles.py`, **antes** del código: `EstadoSesion()` nace con `pendientes == {}` y `cierres_impedidos == 0`; la negación por umbral de `TRX-002` (CLI-001 verificado) deja `pendientes == {"TRX-002": "umbral"}`; negar la misma transacción dos veces deja una sola entrada; las negaciones `SIN_IDENTIDAD`, `CLIENTE_DISTINTO`, `TRANSACCION_NO_CONFIRMADA` y `FALLA_CONTROL` no crean pendientes. Verlo fallar
- [ ] T005 En `src/agente_disputas/controles.py`: `EstadoSesion.pendientes: dict[str, str]` ("transacción → causa", causa en `umbral`, `fuera_de_politica`) y `cierres_impedidos: int = 0`; constantes `UMBRAL = "umbral"`, `FUERA_DE_POLITICA = "fuera_de_politica"`, `MAXIMO_CIERRES_IMPEDIDOS = 2`; `Decision.pendiente: str | None = None` (id de la transacción en la negación `REQUIERE_ANALISTA`); `antes_de_herramienta` registra `pendientes[decision.pendiente] = UMBRAL` al negar. En `src/core_bancario_mcp/bloqueo_escalamiento.py`, renombrar `_lista_de_ids` a `lista_de_ids` (pública, mismo comportamiento) y actualizar sus usos. Dejar verde

---

## Phase 3: User Story 1 - Un escalamiento obligatorio no se puede omitir (Priority: P1) 🎯 MVP

**Goal**: FR-001 a FR-005 ([contracts/escalamiento-pendiente.md](contracts/escalamiento-pendiente.md)).

**Independent Test**: `uv run pytest src/agente_disputas/test_controles.py -k "pendiente or terminar or escal or mensaje"`.

- [ ] T006 [US1] En `src/agente_disputas/test_controles.py`, casos 2 a 5 y 7 del contrato: `despues_de_disputar` con `{"ok": false, "error": {"tipo": "negocio", "codigo": "FUERA_DE_POLITICA", ...}}` para `" TRX-006 "` → `pendientes["TRX-006"] == "fuera_de_politica"`; con `REQUIERE_ANALISTA` → `"umbral"`; con éxito, `TRANSACCION_YA_DISPUTADA` u otro código, respuesta ilegible o `tool_input` sin `transaccion_id` → nada. `antes_de_terminar` sin pendientes → `{}`; con pendiente → `{"decision": "block", "reason": ...}` cuya razón contiene `TRX-002` y `umbral` y no contiene montos, dos veces; la tercera → `{}` con el pendiente intacto y `cierres_impedidos == 2`. `despues_de_escalar` con `ok: true`, `causa` `"umbral"` y `transacciones` `["TRX-002"]` o `'["TRX-002"]'` → limpia; sin la transacción, con causa `"otra"`, con `ok: false` o ilegible → no limpia; con `TRX-002` y `TRX-006` pendientes, escalar solo `TRX-002` deja `TRX-006`; un escalamiento exitoso con causa `persona_solicitada` y sin cliente ni transacciones no limpia ningún pendiente (ajuste L3). `al_recibir_mensaje` vacía `pendientes` y pone `cierres_impedidos` en 0. Entradas `None` o `tool_input` no dict en los cuatro callbacks → `{}` sin cambiar el estado. Verlo fallar
- [ ] T007 [US1] En `src/agente_disputas/controles.py`: `ESCALAR = PREFIJO + "escalar_a_analista"`; `despues_de_disputar`, `despues_de_escalar` (usa `lista_de_ids` del core y compara `causa.strip()`), `antes_de_terminar` (razón en español con cada `TRX (causa …)` y el pedido de handoff completo: cliente, transacciones, acciones realizadas y acción recomendada) y `al_recibir_mensaje`, todos con `try/except` que devuelve `{}` sin cambiar el estado (`# noqa: BLE001`: en `antes_de_terminar`, dejar terminar es la falla abierta justificada en research R4). `hooks()` agrega `PostToolUse` para `iniciar_disputa` y `escalar_a_analista`, `Stop` y `UserPromptSubmit` (matcher `None`), con `timeout=TIEMPO_MAXIMO_SEGUNDOS`. Dejar verde
- [ ] T008 [US1] En `src/agente_disputas/test_configuracion.py`: `opciones.hooks` tiene exactamente los eventos `PreToolUse`, `PostToolUse`, `Stop` y `UserPromptSubmit`; los matchers de `PostToolUse` son exactamente los nombres completos de `verificar_identidad`, `iniciar_disputa` y `escalar_a_analista`; `Stop` y `UserPromptSubmit` con matcher `None`. Escribirlo tras T007 (ajuste L2: depende de los hooks nuevos)
- [ ] T009 [US1] En `src/agente_disputas/test_cli.py`, **antes** del código: `conversar` con un `ClienteFalso` de un turno completado y `controles` cuyo estado tiene un pendiente → escribe la respuesta y después `cli.AVISO_ESCALAMIENTO_PENDIENTE`; sin pendientes o sin `controles` → no lo escribe. Verlo fallar
- [ ] T010 [US1] En `src/agente_disputas/cli.py`: `AVISO_ESCALAMIENTO_PENDIENTE = "No pude pasar tu caso a un analista en este momento. Por favor, inténtalo de nuevo más tarde."`; `conversar(cliente, leer, escribir, controles=None)` lo escribe tras la respuesta si quedan pendientes; `_ejecutar` crea `Controles.desde_entorno(entorno)`, los pasa a `crear_opciones` y a `conversar`. Dejar verde. Commit `feat(#10): escalamiento pendiente con hook Stop y tope`

---

## Phase 4: User Story 2 - El pendiente no bloquea lo que se puede resolver (Priority: P2)

**Goal**: FR-006, test del mensaje de ejemplo.

**Independent Test**: `uv run pytest src/agente_disputas/test_controles.py -k mensaje_de_ejemplo`.

- [ ] T011 [US2] En `src/agente_disputas/test_controles.py`, caso 6: `test_mensaje_de_ejemplo_el_pendiente_no_impide_lo_resoluble`: CLI-001 verificado; `TRX-002` negada por umbral; `TRX-001` se autoriza y el bloqueo de la 4821 se autoriza (`{}`); `antes_de_terminar` bloquea; tras `despues_de_escalar` exitoso con `TRX-002` y causa `umbral`, `antes_de_terminar` → `{}`. Debe pasar sin cambios de código (R5); si falla, corregir `controles.py`. Commit `test(#10): el pendiente no bloquea lo resoluble`

---

## Phase 5: User Story 3 - Persona a pedido y escalamiento con criterio (Priority: P3)

**Goal**: FR-007, FR-009, FR-010 ([contracts/prompt-y-descripcion.md](contracts/prompt-y-descripcion.md)).

**Independent Test**: `uv run pytest src/core_bancario_mcp src/agente_disputas/test_prompts.py`.

- [ ] T012 [US3] En `src/core_bancario_mcp/test_bloqueo_escalamiento.py`, **antes** del cambio: `DESCRIPCION_ESCALAR` menciona `persona_solicitada`, "de inmediato" y "molest". Verlo fallar
- [ ] T013 [US3] En `src/core_bancario_mcp/bloqueo_escalamiento.py`: `DESCRIPCION_ESCALAR` agrega cuándo no usarla ("No la uses solo porque el cliente esté molesto o insatisfecho; si el caso se puede resolver, como una disputa bajo el umbral o un bloqueo, resuélvelo"). Dejar verde

---

## Phase 6: User Story 4 y 5 - Varios asuntos y ejemplos en el prompt (Priority: P4, P5)

**Goal**: FR-007, FR-008, FR-011 ([contracts/prompt-y-descripcion.md](contracts/prompt-y-descripcion.md)).

**Independent Test**: `uv run pytest src/agente_disputas/test_prompts.py`.

- [ ] T014 [US5] En `src/agente_disputas/test_prompts.py`, **antes** del prompt: `VERSION_PROMPT == "4"`; un bloque `<ejemplos>…</ejemplos>` con entre 3 y 5 apariciones de `"Acción esperada:"`; el prompt menciona `persona_solicitada`, `fuera_de_politica` y "molest"; **separación**: dentro de `<ejemplos>` no aparece ningún `ultimos4` de `tarjetas.json`, ningún monto de `transacciones.json` (como número y con punto de miles), ningún id de cliente, tarjeta o transacción ni documento de los datos (leídos con `importlib.resources` de `core_bancario_mcp/datos`), ni ninguna cadena de más de 20 caracteres de `tests/escenarios/*.py` (extraídas con `ast` de las constantes de texto). Reemplazar el test de versión 3. Verlo fallar
- [ ] T015 [US4] [US5] En `src/agente_disputas/prompts.py`: secciones "Cuándo escalar y cuándo no" (persona a pedido de inmediato con `persona_solicitada`, sin buscar ni verificar, sin `cliente_id` si no se conoce; no escalar disputas bajo el umbral, bloqueos ni por molestia; "una persona" como autora del fraude no es un pedido; handoff completo en umbral y política) y "Varios asuntos" (separar, resolver cada uno, responder una sola vez con el resultado de cada asunto); bloque `<ejemplos>` con 4 ejemplos `Cliente:` / `Acción esperada:` según [research.md R6](research.md), con datos inventados que no existen en el core (p. ej. tarjeta 7730, $95.000, $2.300.000); los ejemplos no escriben la cifra del umbral, dicen "supera el umbral" (ajuste L1: 500.000 es también el monto de TRX-004 y el test de separación lo prohíbe); `VERSION_PROMPT = "4"`; líneas ≤ 95 caracteres; docstring que menciona el hook `Stop` del #10. Dejar verde. Commit `feat(#10): prompt v4 con ejemplos y descripción de escalar`

---

## Phase 7: Verificación

**Purpose**: requiere `ANTHROPIC_API_KEY` en el entorno (nunca se lee ni imprime su valor).

- [ ] T016 Ejecutar `uv run pytest` completo, `ruff check src tests` y `ruff format --check src tests` en verde ([quickstart.md §1](quickstart.md))
- [ ] T017 Ejecutar `uv run pytest -m e2e -s` ([quickstart.md §2](quickstart.md)): los escenarios del #8 y el #9 siguen en verde con el prompt v4
- [ ] T018 Validación manual de [quickstart.md §3](quickstart.md) (a–e) con una sonda que registra herramientas por turno y pendientes al final; anotar el resultado de cada caso en esta tarea. Ajuste M1: después del caso (e), en la misma conversación, enviar un mensaje más y comprobar que `pendientes` quedó vacío y `cierres_impedidos` en 0 (el hook `UserPromptSubmit` se disparó). Si no se dispara, agregar en `src/agente_disputas/cli.py` la llamada `controles.al_recibir_mensaje(...)` antes de cada `cliente.query` (con su test en `test_cli.py`) y documentarlo en research R3. Si un caso falla por el prompt, ajustar el prompt (sin palabras clave) y repetir; si falla por los controles, corregir con su test
- [ ] T019 Pasar `bloquear_pii.py --diff` sobre un archivo con `git diff --unified=0 main...HEAD` sin hallazgos

---

## Phase 8: Cierre con `/abrir-pr`

- [ ] T020 Verificar `uv run pytest` en verde y el árbol limpio
- [ ] T021 Marcar T001 a T021 en `specs/010-escalamiento-criterio-solicitudes/tasks.md` y hacer commit. T022 y T023 se marcan en la rama del issue siguiente
- [ ] T022 El desarrollador ejecuta `/abrir-pr` y aprueba el push y el PR. Esperado: revisión de código `APROBADO`, cumplimiento `APROBADO`, PR con `Closes #10`, CI `guardrails` en verde, issue en *In Review* y comentario de avance
- [ ] T023 Después del merge, hecho por el desarrollador: verificar que el #10 queda cerrado y en *Done*

---

## Dependencies & Execution Order

- **US6 (T001–T003)**: primero. T003 en paralelo con T001–T002.
- **Foundational (T004–T005)**: bloquea US1 y US2.
- **US1 (T006–T010)**: T006 → T007; T008 tras T007; T009 → T010 (la CLI usa los controles).
- **US2 (T011)**: tras T007.
- **US3 (T012–T013)**: después de T005 (ajuste L2: T005 renombra `lista_de_ids` en el mismo
  archivo `bloqueo_escalamiento.py`); independiente del resto de US1.
- **US4/US5 (T014–T015)**: independiente de US1; T014 → T015.
- **Verificación (T016–T019)** y **cierre (T020–T023)**: al final.

### Parallel Opportunities

- T003 con T001–T002; T008 con T009; T012–T013 con US1 a partir de T006.

## Parallel Example: User Story 1

```text
Task: "T008 Registro de hooks en src/agente_disputas/test_configuracion.py"
Task: "T009 Aviso de pendiente en src/agente_disputas/test_cli.py"
```

## Implementation Strategy

### MVP

Foundational + US1 + US2: el escalamiento por umbral o política no se puede omitir y no frena
lo resoluble. Es la garantía determinista del ticket.

### Incremental Delivery

Un commit por fase con el test escrito antes. El prompt v4 se valida al final con la API, junto
con los e2e existentes, porque cambia el comportamiento del modelo.
