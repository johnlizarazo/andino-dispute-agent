---

description: "Lista de tareas del issue #2: Automatización del ciclo en GitHub"
---

# Tasks: Automatización del ciclo en GitHub

**Input**: documentos de diseño en `specs/002-automatizacion-ciclo/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la spec no pide tests de código, y este ticket no agrega código ejecutable. La
validación se hace con los escenarios de [quickstart.md](quickstart.md) y deja evidencia en
GitHub. `uv run pytest` debe seguir en verde.

**Organization**: por historia de usuario, en el orden de implementación del plan: US2
(revisor y `/abrir-pr`) → US1 (`siguiente-ticket`) → US4 (`CLAUDE.md`) → US3 (regla del
Project), y después verificación y cierre.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US4).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: crear las carpetas de las piezas nuevas.

- [X] T001 Crear las carpetas `.claude/agents/`, `.claude/commands/` y `.claude/skills/siguiente-ticket/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: las reglas `allow` que acotan al revisor ([research.md R3](research.md)).

- [X] T002 Agregar a `.claude/settings.json` la clave `permissions.allow` con exactamente `"Bash(git diff *)"`, `"Bash(git log *)"` y `"Bash(git show *)"`, sin alterar `permissions.deny` ni `env`

**Checkpoint**: settings listos para el revisor.

---

## Phase 3: User Story 2 - Abrir el PR tras una revisión independiente (Priority: P2)

**Goal**: el revisor independiente y `/abrir-pr`, que se detiene ante bloqueantes (FR-007 a
FR-012).

**Independent Test**: [quickstart.md §3 y §4](quickstart.md).

- [X] T003 [US2] Crear `.claude/agents/revisor-codigo.md` según [contracts/revisor-codigo.md](contracts/revisor-codigo.md): frontmatter con `name: revisor-codigo`, `description`, `tools: Read, Grep, Glob, Bash` y `permissionMode: dontAsk`. En el cuerpo, en español, qué revisa (los tres puntos del contrato), la restricción de no editar nada y el formato de salida fijo con "`VEREDICTO: BLOQUEADO` si y solo si hay al menos un bloqueante"
- [X] T004 [US2] Crear `.claude/commands/abrir-pr.md` según [contracts/abrir-pr.md](contracts/abrir-pr.md): frontmatter con `description`, `argument-hint`, `disable-model-invocation: true` y `allowed-tools` **sin** `git push` ni `create_pull_request`. En el cuerpo, los 7 pasos del contrato en orden, con los criterios de parada, la idempotencia (reutilizar el PR, omitir estado y comentario ya hechos) y la plantilla "PR abierto" de [contracts/comentarios.md](contracts/comentarios.md)
- [X] T005 [US2] Hacer commit `feat(#2): subagente revisor-codigo y comando /abrir-pr`

**Checkpoint**: revisor y comando listos; se verifican en la fase 7 (necesitan una sesión
nueva para cargarse).

---

## Phase 4: User Story 1 - Tomar el siguiente ticket (Priority: P1)

**Goal**: el comando de inicio de ticket (FR-001 a FR-006).

**Independent Test**: [quickstart.md §6](quickstart.md), que se ejecuta con el issue #3
después del merge de este ticket (T020).

- [X] T006 [US1] Crear `.claude/skills/siguiente-ticket/SKILL.md` según [contracts/siguiente-ticket.md](contracts/siguiente-ticket.md): frontmatter con `name`, `description`, `argument-hint: "[número de issue opcional]"` y `allowed-tools` con las 4 herramientas MCP y los 2 comandos git del contrato, **sin** `context: fork`. En el cuerpo, los 7 pasos en orden: la regla de selección ("Todo, menor número, dependencias de 'Depende de' cerradas"), el cálculo de `NNN-slug`, la idempotencia, la plantilla "Inicio" de [contracts/comentarios.md](contracts/comentarios.md), la invocación de `speckit-specify` y la parada obligatoria antes de `speckit-plan`
- [X] T007 [US1] Hacer commit `feat(#2): skill siguiente-ticket`

**Checkpoint**: la skill existe; su prueba real es T020.

---

## Phase 5: User Story 4 - Flujo y definición de hecho documentados (Priority: P4)

**Goal**: FR-015.

**Independent Test**: [quickstart.md §5](quickstart.md), paso 2 (comentario con ajustes), y
lectura de `CLAUDE.md`.

- [X] T008 [US4] Actualizar la sección "Flujo por ticket" de `CLAUDE.md`. Debe nombrar `/siguiente-ticket` y `/abrir-pr`, mostrar la secuencia completa specify → (clarify) → plan → tasks → analyze → implement (→ converge) y los tres puntos de control, y decir que el merge es la aprobación final. Mantenerlo en "menos de 40 líneas" y sin copiar la constitución
- [X] T009 [US4] Hacer commit `docs(#2): definición de hecho y comandos del ciclo en CLAUDE.md`

---

## Phase 6: User Story 3 - Cierre automático al fusionar (Priority: P3)

**Goal**: FR-013 y FR-014.

**Independent Test**: [quickstart.md §2](quickstart.md) y el merge de este ticket (T019).

- [X] T010 [US3] **El desarrollador** desactiva la regla "Pull request linked to issue" en el Project (⋯ → Workflows) y confirma que "Item closed" sigue activa. El asistente lo verifica por GraphQL (`workflows { name enabled }`) y anota el resultado para el comentario de cierre

---

## Phase 7: Verificación en sesión nueva (US2)

**Purpose**: las piezas de `.claude/` se cargan al iniciar la sesión. **Requiere reiniciar
Claude Code** antes de T011.

- [X] T011 [US2] Verificar que `/siguiente-ticket` y `/abrir-pr` aparecen en `/` y que `revisor-codigo` está disponible ([quickstart.md §1](quickstart.md))
- [X] T012 [US2] Delegar en `revisor-codigo` y comprobar que niega `git status`, permite `git diff main..HEAD --stat` y permite leer `specs/002-automatizacion-ciclo/spec.md` ([quickstart.md §3](quickstart.md)). Si falla, aplicar el fallback (un hook `PreToolUse` en el frontmatter que solo deje pasar `git diff`, `git log` y `git show`), actualizar [contracts/revisor-codigo.md](contracts/revisor-codigo.md) y repetir
- [X] T013 [US2] Prueba de bloqueo ([quickstart.md §4](quickstart.md)):
  - Crear la rama local `999-prueba-revisor` desde `002-automatizacion-ciclo`, con `specs/999-prueba-revisor/spec.md` cuyo título sea exactamente el del issue #2 (`# Feature Specification: Automatización del ciclo en GitHub`), con `Issue: #2` y el requisito "el archivo `demo.txt` MUST decir 'hola'". Agregar un `demo.txt` que diga otra cosa y hacer commit. El título exacto es necesario para que `/abrir-pr` pase sus precondiciones y llegue al revisor.
  - Ejecutar `/abrir-pr`: debe terminar en `BLOQUEADO` sin pedir confirmación de push ni de PR. Si pidiera alguna, el desarrollador la **rechaza** y se registra como falla.
  - Volver a `002-automatizacion-ciclo` y borrar la rama local `999-prueba-revisor` con `git branch -D`.

---

## Phase 8: Cierre del ticket con `/abrir-pr` (FR-016)

- [X] T014 Verificar que `uv run pytest` sigue en verde y que no quedan cambios sin commitear
- [X] T015 Marcar T001 a T015 en `specs/002-automatizacion-ciclo/tasks.md` y hacer commit, para que el árbol quede limpio antes de `/abrir-pr`. T016 y T017 ocurren después del último commit de la rama y se marcan con la fase 9, en la rama del issue #3
- [ ] T016 Ejecutar `/abrir-pr` en `002-automatizacion-ciclo`; el desarrollador aprueba el push y la creación del PR. Esperado: veredicto `APROBADO`, PR con `Closes #2`, issue en *In Review* y comentario "**PR abierto**" con los ajustes de los puntos de control y el resultado de T010
- [ ] T017 Ejecutar `/abrir-pr` otra vez y comprobar que no duplica el PR ni el comentario ni cambia el estado (FR-012)

---

## Phase 9: Después del merge (se registra en GitHub)

**Purpose**: estas tareas ocurren cuando la rama ya está fusionada. Su evidencia queda en
GitHub y sus casillas se marcan en la rama del issue #3.

- [ ] T018 **El desarrollador** fusiona el PR
- [ ] T019 Verificar que el issue #2 queda cerrado y en *Done* sin intervención (SC-001, FR-013)
- [ ] T020 [US1] En `main` actualizado, ejecutar `/siguiente-ticket` sin argumentos ([quickstart.md §6](quickstart.md)). Esperado: elige el #3 explicando por qué, lo mueve a *In Progress*, comenta el inicio, crea la rama `003-...`, genera la spec con `Issue: #3` y se detiene pidiendo revisión (SC-001, SC-004). Después, ejecutar `/siguiente-ticket 3`: debe avisar que el #3 ya está en *In Progress* y pedir confirmación, sin duplicar el comentario de inicio (FR-012)

---

## Dependencies & Execution Order

- **Setup (T001)** → **Foundational (T002)** → **US2 (T003–T005)**: T003 depende de T002,
  porque el revisor se apoya en las reglas `allow`.
- **US1 (T006–T007)** y **US4 (T008–T009)**: independientes de US2 en archivos; siguen el
  orden del plan.
- **US3 (T010)**: acción manual, independiente; debe estar hecha antes de T016.
- **Verificación (T011–T013)**: requiere una sesión nueva y las fases 3 a 5 completas.
- **Cierre (T014–T017)**: requiere la fase 7 en verde.
- **Después del merge (T018–T020)**: requiere el merge.

### Parallel Opportunities

- T003 y T006 (archivos distintos), y T008 en paralelo con ambos.
- T010, la acción manual, puede hacerse en cualquier momento antes de T016.

## Parallel Example

```text
Task: "T003 Crear .claude/agents/revisor-codigo.md"
Task: "T006 Crear .claude/skills/siguiente-ticket/SKILL.md"
Task: "T008 Actualizar CLAUDE.md"
```

## Implementation Strategy

### MVP

US2 (revisor y `/abrir-pr`): es lo que permite cerrar este mismo ticket con su propia
herramienta (FR-016) y bloquear un PR con problemas.

### Incremental Delivery

Un commit por historia. La verificación ocurre en una sesión nueva, el cierre se hace con
`/abrir-pr` real, y después del merge `/siguiente-ticket` se estrena con el issue #3.
