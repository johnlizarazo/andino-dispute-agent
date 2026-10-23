---

description: "Lista de tareas del issue #3: Guardrails de desarrollo"
---

# Tasks: Guardrails de desarrollo

**Input**: documentos de diseño en `specs/003-guardrails-desarrollo/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la spec los pide (FR-006, SC-001 a SC-004). Los tests de cada script se escriben
**antes** que el script y viven junto a él. Ningún test contiene literales con forma de
tarjeta real: los números válidos se generan al correr.

**Organization**: en el orden del plan: US1 → US2 → US3 → US6 → US4 → US5, luego CI,
verificación en una sesión nueva y cierre. Los hooks se activan recién en US6, después de
tener sus tests en verde.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US6).

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Crear las carpetas `plugins/andino-guardrails/.claude-plugin/`, `plugins/andino-guardrails/hooks/`, `plugins/andino-guardrails/agents/`, `plugins/andino-guardrails/skills/revisar-cumplimiento/`, `.claude-plugin/`, `.claude/rules/` y `.github/workflows/`
- [X] T002 En `pyproject.toml`, cambiar `testpaths` a `["src", "tests", "plugins"]` sin tocar `markers` ni `addopts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: no hay prerrequisitos adicionales. Cada historia trae sus propios tests y
scripts, y el empaquetado (US6) reúne lo anterior.

---

## Phase 3: User Story 1 - Ningún dato con forma real entra al repositorio (Priority: P1) 🎯 MVP

**Goal**: FR-001 a FR-007 (el workflow de FR-007 está en la fase 9).

**Independent Test**: `uv run pytest plugins/andino-guardrails/hooks/test_bloquear_pii.py`
y [quickstart.md §2](quickstart.md).

- [X] T003 [US1] Escribir `plugins/andino-guardrails/hooks/test_bloquear_pii.py` **antes** que el script, con:
  - Un helper `tarjeta_valida(longitud, separador)` que genere números válidos por Luhn calculando el dígito verificador sobre un prefijo aleatorio.
  - Un test parametrizado con al menos 20 tarjetas generadas (longitudes 13 a 19, con espacio, guion y sin separador), todas detectadas (SC-001).
  - Al menos 20 casos legítimos sin hallazgos (SC-002): `180000`, `1250000`, `$1.250.000`, `CC-FIC-0001`, secuencias de 16 dígitos que no pasan Luhn construidas al vuelo, el texto "13 a 19 dígitos" y un hash hexadecimal.
  - Documentos detectados, **también generados al correr** con un helper `documento(palabra, digitos, con_puntos)`: "CC" con 8 dígitos aleatorios, "cédula" con 7 dígitos aleatorios y puntos de miles, y "documento" con 10 dígitos aleatorios. Ningún literal con forma de documento queda en el archivo, porque el hook bloquearía editarlo y violaría el principio III.
  - Que la muestra del mensaje no contenga el número completo.
  - `textos_nuevos` con eventos de Write, Edit, MultiEdit y NotebookEdit.
  - Que un JSON inválido en stdin salga con código 2 (fallo cerrado, FR-005).
  - El modo `--diff`: solo cuenta las líneas `+` y sale con 1 si hay hallazgos y con 0 si no.
- [X] T004 [US1] Implementar `plugins/andino-guardrails/hooks/bloquear_pii.py` según [contracts/hooks.md](contracts/hooks.md): solo biblioteca estándar; funciones `luhn_valido`, `buscar_hallazgos` y `textos_nuevos`; modo hook (salida 2 con el mensaje enmascarado) y modo `--diff`; `try/except` global que sale con 2 ante cualquier error
- [X] T005 [US1] Ejecutar `uv run pytest plugins/andino-guardrails/hooks/test_bloquear_pii.py` hasta verde y hacer commit `feat(#3): hook bloquear_pii con tests`

**Checkpoint**: la detección está probada; todavía no se ha activado.

---

## Phase 4: User Story 2 - No hay código sin especificación (Priority: P2)

**Goal**: FR-008 y FR-009.

**Independent Test**: los tests del script y [quickstart.md §3](quickstart.md).

- [X] T006 [P] [US2] Escribir `plugins/andino-guardrails/hooks/test_exigir_spec.py`. Cada test crea un repositorio git temporal (`tmp_path`, `git init`, rama con `git checkout -b`) y fija `CLAUDE_PROJECT_DIR`. Casos:
  - Escritura fuera de `src/` → 0.
  - Bajo `src/` en `main` → 2.
  - En `004-algo` sin carpeta de spec → 2, y el mensaje nombra los faltantes.
  - Con solo `spec.md` → 2.
  - Con los tres artefactos → 0.
  - JSON inválido → 2.
- [X] T007 [US2] Implementar `plugins/andino-guardrails/hooks/exigir_spec.py` según [contracts/hooks.md](contracts/hooks.md) y dejar verdes sus tests

---

## Phase 5: User Story 3 - El código queda formateado tras cada edición (Priority: P3)

**Goal**: FR-010 y FR-011.

**Independent Test**: los tests del script y [quickstart.md §4](quickstart.md).

- [X] T008 [P] [US3] Escribir `plugins/andino-guardrails/hooks/test_formatear.py`. Casos:
  - Un `.py` mal formateado en `tmp_path` queda formateado y sale con 0.
  - Un archivo que no es `.py` no se toca y sale con 0.
  - Un `.py` con un problema no corregible (por ejemplo, un nombre no definido, F821) sale con 2 y lo reporta por stderr.
  - Un archivo inexistente sale con 0.
- [X] T009 [US3] Implementar `plugins/andino-guardrails/hooks/formatear.py` según [contracts/hooks.md](contracts/hooks.md) y dejar verdes sus tests
- [X] T010 [US3] Ejecutar `uv run pytest` completo en verde y hacer commit `feat(#3): hooks exigir_spec y formatear con tests`

---

## Phase 6: User Story 6 - Garantías empaquetadas y consumidas por el repositorio (Priority: P6)

**Goal**: FR-018 a FR-020. Al terminar esta fase, los hooks se activan en la sesión (con
`/reload-plugins` o en la sesión siguiente).

**Nota**: desde aquí los hooks evalúan también las ediciones de este ticket (T017 a T026).
Un bloqueo inesperado se trata como hallazgo, que se corrige o se documenta; nunca se
desactiva el hook para esquivarlo.

**Independent Test**: [quickstart.md §1](quickstart.md).

- [X] T011 [P] [US6] Crear `plugins/andino-guardrails/.claude-plugin/plugin.json` exactamente como en [contracts/plugin-marketplace.md](contracts/plugin-marketplace.md), "sin `version`"
- [X] T012 [P] [US6] Crear `plugins/andino-guardrails/hooks/hooks.json` exactamente como en [contracts/hooks.md](contracts/hooks.md)
- [X] T013 [P] [US6] Crear `.claude-plugin/marketplace.json` exactamente como en [contracts/plugin-marketplace.md](contracts/plugin-marketplace.md)
- [X] T014 [US6] En `.claude/settings.json`, agregar `extraKnownMarketplaces.banco-andino` con fuente `directory` y `path: "./"`, `enabledPlugins` con `"andino-guardrails@banco-andino": true` y `"Bash(uv run pytest *)"` en `permissions.allow`, sin alterar lo existente
- [X] T015 [P] [US6] Crear `plugins/andino-guardrails/README.md` con lo que exige [contracts/plugin-marketplace.md](contracts/plugin-marketplace.md): qué trae el plugin, sus requisitos, cómo refrescarlo (`/reload-plugins` o una sesión nueva) y la garantía del auditor
- [X] T016 [US6] Ejecutar `claude plugin validate ./` y `claude plugin validate ./plugins/andino-guardrails` sin errores, y hacer commit `feat(#3): plugin andino-guardrails y marketplace banco-andino`

---

## Phase 7: User Story 4 - Revisión de cumplimiento antes del PR (Priority: P4)

**Goal**: FR-012 a FR-015.

**Independent Test**: [quickstart.md §5](quickstart.md).

- [X] T017 [P] [US4] Crear `plugins/andino-guardrails/agents/auditor-cumplimiento.md` según [contracts/cumplimiento.md](contracts/cumplimiento.md): `tools: Read, Grep, Glob, Bash`, sin `permissionMode`, y los 7 puntos del cuerpo, incluidos "NO APLICA" y el formato de veredicto del [data-model](data-model.md#veredicto-de-cumplimiento)
- [X] T018 [P] [US4] Crear `plugins/andino-guardrails/skills/revisar-cumplimiento/SKILL.md` según [contracts/cumplimiento.md](contracts/cumplimiento.md): `context: fork`, `agent: andino-guardrails:auditor-cumplimiento`, `background: false`, `allowed-tools` y `argument-hint`, con un cuerpo autocontenido
- [X] T019 [US4] En `.claude/commands/abrir-pr.md`:
  - Agregar el paso **2b**: invocar `andino-guardrails:revisar-cumplimiento` y detenerse sin publicar si el veredicto es `BLOQUEADO`.
  - Agregar el veredicto de cumplimiento a la sección "Revisión independiente" de la plantilla del comentario.
  - Agregar el veredicto de cumplimiento al cuerpo del PR.
- [X] T020 [US4] Hacer commit `feat(#3): auditor-cumplimiento, skill revisar-cumplimiento y paso de cumplimiento en /abrir-pr`

---

## Phase 8: User Story 5 - Convenciones por ruta (Priority: P5)

**Goal**: FR-016 y FR-017.

**Independent Test**: [quickstart.md §6](quickstart.md).

- [X] T021 [P] [US5] Crear `.claude/rules/tests.md` con el `paths` y el contenido de [contracts/rules.md](contracts/rules.md)
- [X] T022 [P] [US5] Crear `.claude/rules/herramientas-mcp.md` con el `paths` y el contenido de [contracts/rules.md](contracts/rules.md)
- [X] T023 [US5] Hacer commit `feat(#3): rules de tests y de herramientas MCP`

---

## Phase 9: CI y documentación

- [X] T024 [P] Crear `.github/workflows/guardrails.yml` según [contracts/ci.md](contracts/ci.md), con las versiones vigentes de `actions/checkout` y `astral-sh/setup-uv` (consultadas con `gh api repos/<action>/releases/latest`)
- [X] T025 [P] Agregar al `README.md` una sección "Guardrails" que diga qué bloquea el plugin, dónde viven las rules y que el CI repite el chequeo de datos sobre el diff
- [X] T026 Hacer la prueba negativa local de [quickstart.md §7](quickstart.md), paso 2: generar un diff temporal con una tarjeta válida en una línea `+` y comprobar que `bloquear_pii.py --diff` sale con 1. Borrar el archivo temporal y hacer commit `ci(#3): workflow guardrails y README`

---

## Phase 10: Verificación en sesión nueva

**Purpose**: el plugin y las rules se cargan al iniciar la sesión. **Requiere reiniciar la
app y aceptar la confianza de la carpeta** antes de T027.

- [ ] T027 [US6] Comprobar en `/plugin` que `andino-guardrails@banco-andino` está habilitado ([quickstart.md §1](quickstart.md)). Si la fuente `directory` no funciona, aplicar el fallback `github` de [contracts/plugin-marketplace.md](contracts/plugin-marketplace.md), documentarlo en `research.md` R3 y repetir
- [ ] T028 [US1] Ejecutar [quickstart.md §2](quickstart.md). Los textos con forma real los genera un script de Python ejecutado en la consola (nunca escritos por el asistente como literales), y se le pide al asistente que los escriba con Write: se bloquean. Los casos legítimos se permiten. Medir que el hook responde en menos de 2 s
- [ ] T029 [US2] Ejecutar [quickstart.md §3](quickstart.md): permitido en la rama del ticket, bloqueado en una rama local `998-sin-spec` (borrarla al terminar)
- [ ] T030 [US3] Ejecutar [quickstart.md §4](quickstart.md) y borrar el archivo de prueba. SC-004 se cubre con los tests de T008 (todos los casos) y con esta prueba real de un archivo
- [ ] T031 [US4] Ejecutar [quickstart.md §5](quickstart.md), paso 1: `/andino-guardrails:revisar-cumplimiento` devuelve `APROBADO`, con las reglas en "NO APLICA". Si `agent:` falla, aplicar el fallback de [contracts/cumplimiento.md](contracts/cumplimiento.md) y repetir
- [ ] T032 [US4] Ejecutar [quickstart.md §5](quickstart.md), paso 3:
  - Crear la rama local `997-prueba-cumplimiento` desde `003-guardrails-desarrollo` y copiar `spec.md`, `plan.md` y `tasks.md` de `specs/003-guardrails-desarrollo/` a `specs/997-prueba-cumplimiento/`, conservando el título y la línea `**Issue**: #3`. Así el revisor de código no bloquea por falta de artefactos en el paso 2.
  - Agregar un test que falle a propósito (`assert False`) en `plugins/andino-guardrails/hooks/test_bloquear_pii.py` y hacer commit. El desarrollador ejecuta `/abrir-pr`.
  - Si el revisor de código igualmente bloquea en el paso 2, invocar directamente `/andino-guardrails:revisar-cumplimiento` sobre la rama y registrar que devuelve `BLOQUEADO`.
  - Esperado: se detiene en el paso 2b sin publicar. Si apareciera una confirmación de push o de PR, se **rechaza** y se registra como falla.
  - Borrar la rama.
- [ ] T033 [US5] Ejecutar [quickstart.md §6](quickstart.md): leer un `test_*.py` del plugin y confirmar que la rule de tests se carga

---

## Phase 11: Cierre con `/abrir-pr`

- [ ] T034 Verificar `uv run pytest` en verde y el árbol limpio
- [ ] T035 Marcar T001 a T035 en `specs/003-guardrails-desarrollo/tasks.md` y hacer commit. Las tareas T036 en adelante ocurren después del último commit de la rama y se marcan en la rama del issue siguiente
- [ ] T036 El desarrollador ejecuta `/abrir-pr`, que ahora incluye cumplimiento, y aprueba el push y el PR. Esperado:
  - Revisión de código `APROBADO`.
  - Cumplimiento `APROBADO`.
  - PR con `Closes #3`.
  - El job `guardrails` del PR pasa.
  - Issue en *In Review* y comentario de avance con los dos veredictos.
- [ ] T037 Después del merge, hecho por el desarrollador: verificar que el issue #3 queda cerrado y en *Done* sin intervención

---

## Dependencies & Execution Order

- **Setup (T001–T002)** → **US1 (T003–T005)**. Los tests van antes que el script (T003 → T004).
- **US2 (T006–T007)** y **US3 (T008–T009)**: en paralelo entre sí, después de US1. T010 cierra
  ambas.
- **US6 (T011–T016)**: después de US1 a US3, porque activa los hooks.
- **US4 (T017–T020)** y **US5 (T021–T023)**: independientes entre sí, después de US6.
- **CI (T024–T026)**: después de US1, porque usa `bloquear_pii.py`.
- **Verificación (T027–T033)**: requiere reiniciar la sesión con todo lo anterior hecho.
- **Cierre (T034–T037)**: requiere la verificación en verde.

### Parallel Opportunities

- T006 y T008; T011, T012, T013 y T015; T017 y T018; T021 y T022; T024 y T025.

## Parallel Example: User Story 6

```text
Task: "T011 Crear plugins/andino-guardrails/.claude-plugin/plugin.json"
Task: "T012 Crear plugins/andino-guardrails/hooks/hooks.json"
Task: "T013 Crear .claude-plugin/marketplace.json"
Task: "T015 Crear plugins/andino-guardrails/README.md"
```

## Implementation Strategy

### MVP

US1 (bloqueo de datos con forma real, con tests): elimina la falta grave más probable.

### Incremental Delivery

Un commit por historia. Los hooks se activan cuando ya están probados (US6), la verificación
ocurre en una sesión nueva, y el cierre se hace con un `/abrir-pr` que ya incluye la revisión
de cumplimiento.
