# Implementation Plan: Guardrails de desarrollo

**Branch**: `003-guardrails-desarrollo` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-guardrails-desarrollo/spec.md` (issue #3)

## Summary

El plugin `andino-guardrails`, publicado en el marketplace `banco-andino` del propio
repositorio y consumido por él, contiene:

- **Tres hooks**:
  - `bloquear_pii` (`PreToolUse`): datos con forma real.
  - `exigir_spec` (`PreToolUse`): spec-first bajo `src/`.
  - `formatear` (`PostToolUse`): `ruff format` y `ruff check --fix`.
- **El subagente `auditor-cumplimiento`** y **la skill `revisar-cumplimiento`**
  (`context: fork`).

Fuera del plugin:

- Las rules `tests.md` y `herramientas-mcp.md` van en `.claude/rules/`, porque los plugins
  no pueden traer rules.
- Un workflow de GitHub reutiliza `bloquear_pii` en modo CLI para los commits externos.
- `/abrir-pr` agrega la revisión de cumplimiento.

Todas las decisiones están en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14, con solo la biblioteca estándar en los scripts de hooks;
Markdown con frontmatter para el agente, la skill y las rules; JSON para el manifiesto y el
marketplace; YAML para el workflow

**Primary Dependencies**: Claude Code 2.1.x (plugins, hooks, rules); `uv`; `ruff` (ya en el
grupo `dev`); GitHub Actions

**Storage**: N/A

**Testing**: `pytest` con tests junto a cada script en `plugins/andino-guardrails/hooks/`,
más los escenarios de [quickstart.md](quickstart.md) en una sesión real

**Target Platform**: Claude Code en Windows (hooks por Git Bash), Linux y macOS;
`ubuntu-latest` en CI

**Project Type**: plugin de Claude Code más configuración del repositorio

**Performance Goals**: cada hook termina en menos de 2 s, para que no se note en la edición

**Constraints**:
- Los hooks fallan cerrados: solo el código 2 bloquea, así que todo error termina en 2 (R4).
- Los agentes de plugins ignoran `permissionMode` (R9).
- Los plugins no traen rules (R2).
- Ningún literal de tarjeta en el repositorio (FR-006).

**Scale/Scope**: 3 scripts con sus tests, 1 agente, 1 skill, 2 rules, 1 workflow, el
manifiesto y el marketplace, y cambios en `.claude/settings.json`, `pyproject.toml`,
`/abrir-pr` y el README

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | El auditor las verifica antes de cada PR (FR-014); hoy reporta "no aplica" porque no hay código de negocio. | ✅ |
| II. Garantías deterministas | Datos, spec-first y formato son hooks que fallan cerrados; el cumplimiento, que requiere juicio, es un subagente aislado. La garantía más débil del auditor en el plugin queda declarada (R9). | ✅ |
| III. Datos ficticios y cero credenciales | Es el objetivo de US1. Tests con números generados al correr; el CI no usa secretos. | ✅ |
| IV. Spec-first | US2 lo vuelve determinista. Este ticket no escribe en `src/`. | ✅ |
| V. Contrato de herramientas | La rule `herramientas-mcp.md` lleva el contrato a cada archivo del servidor. | ✅ |
| VI. Tests junto al código | Tests junto a cada script; `uv run pytest` incluye `plugins/` y corre en CI. | ✅ |
| VII. Simplicidad y trazabilidad | Un mecanismo por necesidad (R1); un solo script de datos para dentro y fuera del asistente (R6). | ✅ |

**Resultado**: todos los gates pasan.

**Re-evaluación tras el diseño (fase 1)**: sin cambios. Tres puntos no están verificados y
tienen prueba y fallback: la fuente `directory` con `./` (R3), `agent:` con espacio de
nombres (R10) y el esquema de MultiEdit (R4).

## Project Structure

### Documentation (this feature)

```text
specs/003-guardrails-desarrollo/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── hooks.md                 # entrada, salida y reglas de los 3 hooks
│   ├── plugin-marketplace.md    # manifiesto, marketplace y settings
│   ├── cumplimiento.md          # auditor, skill y cambio en /abrir-pr
│   ├── rules.md                 # las 2 rules
│   └── ci.md                    # workflow
├── checklists/requirements.md
└── tasks.md                     # /speckit-tasks
```

### Source Code (repository root)

```text
.
├── .claude-plugin/
│   └── marketplace.json                     # nuevo: marketplace banco-andino
├── plugins/andino-guardrails/
│   ├── .claude-plugin/plugin.json           # nuevo
│   ├── hooks/
│   │   ├── hooks.json                       # nuevo: registro de los 3 hooks
│   │   ├── bloquear_pii.py                  # nuevo (también CLI para CI)
│   │   ├── test_bloquear_pii.py             # nuevo
│   │   ├── exigir_spec.py                   # nuevo
│   │   ├── test_exigir_spec.py              # nuevo
│   │   ├── formatear.py                     # nuevo
│   │   └── test_formatear.py                # nuevo
│   ├── agents/auditor-cumplimiento.md       # nuevo
│   ├── skills/revisar-cumplimiento/SKILL.md # nuevo
│   └── README.md                            # nuevo: qué trae y cómo refrescarlo
├── .claude/
│   ├── settings.json                        # mod: marketplace, plugin, allow pytest
│   ├── rules/tests.md                       # nuevo
│   ├── rules/herramientas-mcp.md            # nuevo
│   └── commands/abrir-pr.md                 # mod: paso 2b de cumplimiento
├── .github/workflows/guardrails.yml         # nuevo
├── pyproject.toml                           # mod: testpaths con "plugins"
└── README.md                                # mod: sección "Guardrails"
```

**Structure Decision**: lo reutilizable (hooks, auditor, skill) va en el plugin; lo propio de
este repositorio (rules, `/abrir-pr`, el revisor) se queda en `.claude/`. Los tests van junto
a cada script. Ver [research.md R1 y R2](research.md).

## Orden de implementación

1. **US1, datos**: `bloquear_pii.py` con sus tests **primero**, antes de activar nada, porque
   una vez activo el hook evalúa también los archivos de este ticket.
2. **US2 y US3**: `exigir_spec.py` y `formatear.py`, con sus tests.
3. **US6, empaquetado**: `plugin.json`, `hooks.json`, `marketplace.json` y settings. Se
   verifica que la fuente `directory` funciona (R3).
4. **US4, cumplimiento**: el auditor, la skill y el paso 2b de `/abrir-pr`.
5. **US5, rules**: las dos rules.
6. **CI**: el workflow.
7. **Verificación en una sesión nueva** y cierre con `/abrir-pr`, que esta vez incluye
   cumplimiento.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| La fuente `directory` con `./` no se resuelve | Prueba en el paso 3; fallback con fuente `github` (R3). |
| `agent:` no acepta `andino-guardrails:auditor-cumplimiento` | Prueba; fallback con `general-purpose` y las instrucciones en la skill (R10). |
| El hook de datos da falsos positivos sobre archivos del propio repositorio | Batería de casos legítimos en los tests (SC-002); el CI revisa solo el diff. |
| Un hook lento entorpece la edición | Solo biblioteca estándar y `uv run --no-project`; se mide en la verificación. |
| El hook de spec-first bloquea el trabajo de este mismo ticket | Este ticket no escribe en `src/`. |
| El auditor en el plugin tiene una garantía más débil que el revisor | Se declara en el contrato y en el README del plugin (R9). |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
