---

description: "Lista de tareas del issue #1: Bootstrap del proceso"
---

# Tasks: Bootstrap del proceso

**Input**: documentos de diseño en `specs/001-bootstrap-proceso/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la spec no pide TDD. Los únicos tests de código son los de humo de importación
que exige el plan (R9), dentro de US4. El resto se valida con los escenarios de
[quickstart.md](quickstart.md).

**Organization**: tareas agrupadas por historia de usuario, en el orden de implementación
del plan: US1 → US2 → US4 → US3, más una fase final de verificación en una sesión nueva.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US4).
- Rutas relativas a la raíz del repositorio.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: normalizar finales de línea antes de crear archivos nuevos, en un commit propio
para no mezclar un diff grande con el resto (plan, Riesgos).

- [ ] T001 Crear `.gitattributes` con exactamente `* text=auto eol=lf` y `*.ps1 text eol=crlf` (ver [contracts/gitignore.md](contracts/gitignore.md))
- [ ] T002 Ejecutar `git add --renormalize .`, comprobar con `git ls-files --eol` que los archivos de texto quedan `i/lf` (salvo `.ps1`) y hacer commit `chore(#1): normalizar finales de línea` que solo contenga `.gitattributes` y la renormalización

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: no hay prerrequisitos bloqueantes adicionales. Spec Kit, la constitución y el
repositorio público ya existen (supuestos de la spec). Las historias empiezan directamente.

---

## Phase 3: User Story 1 - Los secretos quedan fuera de alcance (Priority: P1) 🎯 MVP

**Goal**: ningún `.env*` puede versionarse ni ser leído o editado por el asistente
(FR-001 a FR-004).

**Independent Test**: [quickstart.md §1](quickstart.md#1-secretos-fuera-de-alcance-us1--fr-001-a-fr-004--sc-001-sc-002).
Los pasos de git se validan aquí (T006); los intentos del asistente se validan en una
sesión nueva (T020).

- [ ] T003 [P] [US1] Ampliar `.gitignore` con las entradas obligatorias de [contracts/gitignore.md](contracts/gitignore.md): `.env`, `.env.*`, `!.env.example`, `CLAUDE.local.md`, `.claude/settings.local.json`, conservando las de Python ya presentes
- [ ] T004 [P] [US1] Crear `.claude/settings.json` con la lista `permissions.deny` exacta de [contracts/claude-settings.md](contracts/claude-settings.md). Restricciones: "Ninguna regla `Write(...)`" y "la negación `!.env.example` aparece después de las reglas sin ancla que excepciona"
- [ ] T005 [P] [US1] Crear `.env.example` con `GITHUB_PAT=` y `ANTHROPIC_API_KEY=` "sin valores, con un comentario de propósito para cada una"
- [ ] T006 [US1] Validar con `git check-ignore -v --no-index` (sobre rutas, sin crear archivos: el asistente no puede crear `.env` una vez activas las reglas de T004) que coinciden `.env`, `.env.local`, `config/.env`, `CLAUDE.local.md` y `.claude/settings.local.json`, y que `.env.example` no coincide; hacer commit `chore(#1): proteger secretos (gitignore, permisos, .env.example)`

**Checkpoint**: los secretos ya no pueden versionarse, y las reglas de permisos quedan
listas para la sesión siguiente.

---

## Phase 4: User Story 2 - Convenciones del equipo al clonar (Priority: P2)

**Goal**: quien clona recibe la constitución y unos comandos de Spec Kit que funcionan en
cualquier sistema operativo; lo personal queda aislado (FR-005 a FR-009).

**Independent Test**: [quickstart.md §2](quickstart.md#2-convenciones-al-clonar-us2--fr-005-a-fr-009--sc-003-sc-004).

- [ ] T007 [US2] Agregar a `.claude/settings.json` la clave `"env": { "PYTHONUTF8": "1" }` sin alterar `permissions.deny` (depende de T004)
- [ ] T008 [P] [US2] Crear `CLAUDE.md` en la raíz, de "menos de 40 líneas", que importe la constitución con `@.specify/memory/constitution.md` sin copiar su texto, liste los comandos clave (`uv sync`, `uv run pytest`, `uv run pytest -m e2e`) y resuma el flujo con los tres puntos de control humanos
- [ ] T009 [US2] Validar que el script `.venv/Scripts/python.exe .specify/scripts/python/resolve_template.py spec-template --json` termina sin errores con `PYTHONUTF8=1` y falla sin ella (documentar el resultado); hacer commit `chore(#1): CLAUDE.md y entorno compartido con PYTHONUTF8`

**Checkpoint**: una sesión nueva carga la constitución y puede correr Spec Kit sin
configuración manual.

---

## Phase 5: User Story 4 - Estructura base del proyecto (Priority: P4)

**Goal**: el proyecto declara sus dos paquetes y se instala desde cero sin errores
(FR-014 a FR-016). Va antes de US3 para que el reinicio de la sesión ocurra una sola vez,
al final (plan, Orden de implementación).

**Independent Test**: [quickstart.md §3](quickstart.md#3-estructura-base-us4--fr-014-a-fr-016--sc-005).

- [ ] T010 [US4] Eliminar `src/andino_dispute_agent/` (paquete de ejemplo de `uv init`)
- [ ] T011 [P] [US4] Crear `src/agente_disputas/__init__.py` con solo un docstring que describa el paquete (agente de disputas con Claude Agent SDK)
- [ ] T012 [P] [US4] Crear `src/core_bancario_mcp/__init__.py` con solo un docstring que describa el paquete (servidor MCP que simula el core bancario con datos ficticios)
- [ ] T013 [P] [US4] Crear `src/agente_disputas/test_paquete.py` con un test de humo que importe `agente_disputas` y verifique que tiene docstring
- [ ] T014 [P] [US4] Crear `src/core_bancario_mcp/test_paquete.py` con un test de humo que importe `core_bancario_mcp` y verifique que tiene docstring
- [ ] T015 [US4] Actualizar `pyproject.toml`: descripción real (la del repositorio), eliminar `[project.scripts]` del paquete de ejemplo, agregar `[tool.uv.build-backend] module-name = ["agente_disputas", "core_bancario_mcp"]` y `[tool.pytest.ini_options]` con `testpaths = ["src", "tests"]`, el marcador `e2e` registrado y `addopts = "-m 'not e2e'"` (research R6 y R9)
- [ ] T016 [US4] Borrar `.venv`, ejecutar `uv sync` y medir que termina en menos de 2 minutos; ejecutar `uv run pytest` y comprobar que pasan los 2 tests con código 0; hacer commit `chore(#1): paquetes agente_disputas y core_bancario_mcp` incluyendo `uv.lock`

**Checkpoint**: estructura lista para los issues del servidor y del agente.

---

## Phase 6: User Story 3 - El asistente opera el Project de GitHub (Priority: P3)

**Goal**: conexión MCP de GitHub declarada sin credenciales y documentada (FR-010 a
FR-012). La verificación de escritura (FR-013) va en la fase 7.

**Independent Test**: [quickstart.md §4](quickstart.md#4-conexión-con-el-project-us3--fr-010-a-fr-013--sc-006).

- [ ] T017 [P] [US3] Crear `.mcp.json` con el servidor `github` exacto de [contracts/mcp-json.md](contracts/mcp-json.md): `type` `http`, URL `https://api.githubcopilot.com/mcp/`, `Authorization: Bearer ${GITHUB_PAT}` sin valor por defecto, y `X-MCP-Toolsets: context,repos,issues,pull_requests,projects`
- [ ] T018 [P] [US3] Reescribir `README.md`: propósito del proyecto (banco ficticio, datos ficticios), requisitos (Python 3.14, `uv`, Claude Code), instalación (`uv sync`, `uv run pytest`) y una sección "Token de GitHub" con el tipo de token (PAT clásico, scopes `repo` y `project`), dónde guardarlo (variable de entorno de usuario `GITHUB_PAT`, nunca en archivos), el comando PowerShell que no deja el token en el historial y el aviso de reiniciar la aplicación por completo
- [ ] T019 [US3] Hacer commit `chore(#1): conexión MCP de GitHub y README`

**Checkpoint**: todo listo para verificar en una sesión nueva.

---

## Phase 7: Verificación en sesión nueva (US1, US2, US3)

**Purpose**: los escenarios que exigen que Claude Code cargue la configuración nueva y vea
`GITHUB_PAT`. **Requiere reiniciar la aplicación por completo** antes de T020.

- [ ] T020 [US1] **El desarrollador** crea a mano un `.env` en la raíz con un valor ficticio (`CLAVE_FICTICIA=valor-de-prueba`); el asistente no puede crearlo por las reglas de T004. En la sesión nueva, ejecutar [quickstart.md §1](quickstart.md#1-secretos-fuera-de-alcance-us1--fr-001-a-fr-004--sc-001-sc-002) paso 3: leer, buscar, `cat`, `grep`, `cp`, `Get-Content` y editar deben negarse; leer `.env.example` debe permitirse. Registrar el resultado de cada vía; el desarrollador borra el archivo de prueba
- [ ] T021 [US2] Clonar el repositorio (rama `001-bootstrap-proceso`) en un directorio temporal y, desde allí, ejecutar [quickstart.md §2](quickstart.md#2-convenciones-al-clonar-us2--fr-005-a-fr-009--sc-003-sc-004): la sesión responde el umbral desde la constitución importada, el script de Spec Kit corre sin errores de codificación sin configuración manual, y los archivos personales quedan ignorados (SC-003, SC-004); borrar el clon temporal al terminar
- [ ] T022 [US3] Ejecutar [quickstart.md §4](quickstart.md#4-conexión-con-el-project-us3--fr-010-a-fr-013--sc-006): `/mcp` muestra `github` conectado; con el MCP, mover el issue #1 de *In Progress* a *In Review* y de vuelta, y comentar en el issue #1 el resultado de la verificación (FR-013)
- [ ] T023 Barrer el historial con `git log -p --all` buscando `ghp_`, `gho_` y `github_pat_` (SC-002), y confirmar con `git ls-files .specify/memory/constitution.md .claude/skills` que Spec Kit y la constitución siguen versionados (FR-008, FR-009)

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T024 Marcar las tareas completadas en `specs/001-bootstrap-proceso/tasks.md` y hacer commit
- [ ] T025 Publicar la rama `001-bootstrap-proceso` y crear manualmente el pull request contra `main` con `Closes #1` (el comando `/abrir-pr` nace en el issue #2)
- [ ] T026 Revisar en qué estado dejó el Project al issue #1 tras crear el PR (el workflow "Pull request linked to issue" puede moverlo solo); dejarlo en *In Review*, anotar el comportamiento observado como insumo del issue #2, y comentar qué se especificó, qué se decidió (enlazar `research.md`) y qué quedó pendiente

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (fase 1)**: primero, en su propio commit.
- **US1 (fase 3)**: después del Setup.
- **US2 (fase 4)**: T007 depende de T004, porque es el mismo archivo. T008 es independiente.
- **US4 (fase 5)**: independiente de US1 y US2; va aquí por el orden del plan.
- **US3 (fase 6)**: independiente en archivos; va al final para que el reinicio sea uno solo.
- **Verificación (fase 7)**: depende de las fases 3 a 6 y de reiniciar la aplicación.
- **Polish (fase 8)**: depende de la fase 7.

### User Story Dependencies

- US1, US2, US3 y US4 no dependen funcionalmente entre sí.
- La única dependencia real es de archivo: `.claude/settings.json` (T004 → T007).

### Parallel Opportunities

- **US1:** T003, T004 y T005, porque son archivos distintos.
- **US2:** T008 en paralelo con T007.
- **US4:** T011 a T014, porque son cuatro archivos distintos.
- **US3:** T017 y T018.

## Parallel Example: User Story 4

```text
Task: "T011 Crear src/agente_disputas/__init__.py"
Task: "T012 Crear src/core_bancario_mcp/__init__.py"
Task: "T013 Crear src/agente_disputas/test_paquete.py"
Task: "T014 Crear src/core_bancario_mcp/test_paquete.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Fase 1 (finales de línea), en su propio commit.
2. Fase 3 (US1): el repositorio público queda protegido.
3. **Parar y validar** los pasos de git (T006).

### Incremental Delivery

Un commit por fase, siguiendo el orden del plan: US1 → US2 → US4 → US3. Al final, la
verificación en una sesión nueva y el pull request que cierra el issue #1.
