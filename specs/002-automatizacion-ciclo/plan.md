# Implementation Plan: Automatización del ciclo en GitHub

**Branch**: `002-automatizacion-ciclo` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-automatizacion-ciclo/spec.md` (issue #2)

## Summary

Tres piezas versionadas de Claude Code y una regla del Project cubren el ciclo del ticket:

- **Skill `siguiente-ticket`**: elige el issue, lo mueve a *In Progress*, comenta el inicio,
  crea la rama `NNN-slug` y lanza `speckit-specify`. Se detiene en la spec.
- **Subagente `revisor-codigo`**: revisa el diff contra la spec. Tiene contexto aislado,
  solo lectura y Git acotado a `diff`, `log` y `show`.
- **Comando `/abrir-pr`**: invoca al revisor, se detiene si hay bloqueantes y, si no los
  hay, publica la rama, crea el PR con `Closes #N`, pasa el issue a *In Review* y comenta.
- **Regla integrada "Item closed"**: pasa el issue a *Done* al fusionar. La regla de PR
  vinculados se desactiva.

La definición de hecho se completa en `CLAUDE.md`. Todas las decisiones están en
[research.md](research.md).

## Technical Context

**Language/Version**: Markdown con frontmatter YAML (skills, comandos y subagentes de Claude
Code); no hay código Python nuevo

**Primary Dependencies**: Claude Code 2.1.x; servidor MCP de GitHub (`.mcp.json`, issue #1);
Spec Kit 1.2 (`speckit-specify`)

**Storage**: N/A. El estado vive en GitHub (issues, Project, PR) y en git (ramas, `specs/`).

**Testing**: validación manual guiada por [quickstart.md](quickstart.md), con evidencia en
GitHub. No hay tests de código porque no hay código ejecutable nuevo.

**Target Platform**: sesiones de Claude Code en Windows, Linux y macOS

**Project Type**: configuración del flujo de desarrollo (ecosistema de Claude Code)

**Performance Goals**: iniciar un ticket con un solo comando (SC-004)

**Constraints**:
- `allowed-tools` pre-aprueba pero no restringe (R2).
- El campo `tools` de un subagente no acepta patrones de Bash (R3).
- Publicar solo a pedido del desarrollador (R4).
- Sin duplicados al reintentar (R7).

**Scale/Scope**: 3 archivos de Claude Code nuevos, 2 archivos modificados (`CLAUDE.md` y
`.claude/settings.json`) y 1 ajuste manual en el Project

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | No las toca; la revisión de cumplimiento es del issue #3. | ✅ N/A |
| II. Garantías deterministas | Lo que no debe fallar es declarativo: `dontAsk` + `allow` acotan al revisor, y `disable-model-invocation` impide que el modelo publique solo. Las instrucciones guían el flujo; no garantizan seguridad. | ✅ |
| III. Datos ficticios y cero credenciales | Los comandos usan el MCP con `${GITHUB_PAT}`, sin tokens nuevos. Se descartó la GitHub Action porque exigiría otro secreto. | ✅ |
| IV. Spec-first | El ticket tiene spec, plan y tareas. Además, `siguiente-ticket` automatiza que cada ticket nazca con su spec enlazada al issue, y `/abrir-pr` garantiza `Closes #N`. | ✅ |
| V. Contrato de herramientas | Sin herramientas MCP propias. | ✅ N/A |
| VI. Tests junto al código | No hay código nuevo. La validación es por escenarios con evidencia en GitHub. `uv run pytest` sigue en verde. | ✅ |
| VII. Simplicidad y trazabilidad | Tres piezas, una por responsabilidad. Se reutiliza la regla integrada del Project en vez de una Action, y el revisor se acota de forma declarativa en vez de con un hook. Cada decisión queda en `research.md`. | ✅ |

**Resultado**: todos los gates pasan.

**Re-evaluación tras el diseño (fase 1)**: sin cambios. Los contratos solo concretan las
piezas evaluadas. La única dependencia no verificada (`dontAsk` con Read, Grep y Glob)
tiene verificación explícita y un fallback documentado (R3).

## Project Structure

### Documentation (this feature)

```text
specs/002-automatizacion-ciclo/
├── spec.md
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones y alternativas
├── data-model.md        # Fase 1: entidades del ciclo y transiciones de estado
├── quickstart.md        # Fase 1: guía de validación
├── contracts/
│   ├── siguiente-ticket.md
│   ├── revisor-codigo.md
│   ├── abrir-pr.md
│   └── comentarios.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
.
├── CLAUDE.md                              # modificado: definición de hecho y comandos del ciclo
└── .claude/
    ├── settings.json                      # modificado: permissions.allow para git diff/log/show
    ├── skills/
    │   └── siguiente-ticket/
    │       └── SKILL.md                   # nuevo
    ├── agents/
    │   └── revisor-codigo.md              # nuevo
    └── commands/
        └── abrir-pr.md                    # nuevo
```

Más un ajuste manual en GitHub: desactivar la regla "Pull request linked to issue" del
Project.

**Structure Decision**: piezas de equipo en `.claude/`, versionadas. No van al plugin
todavía: el issue #3 decide qué se empaqueta. El revisor queda en `.claude/agents/` porque
está atado al flujo de este repositorio ([research.md R1](research.md)).

## Orden de implementación

1. **Revisor** (P2): `.claude/agents/revisor-codigo.md` y las reglas `allow` en settings.
   Va primero porque `/abrir-pr` depende de él y su verificación (R3) puede obligar al
   fallback.
2. **`/abrir-pr`** (P2): `.claude/commands/abrir-pr.md`.
3. **`siguiente-ticket`** (P1): `.claude/skills/siguiente-ticket/SKILL.md`. Va después
   porque su prueba real (iniciar el issue #3) conviene hacerla cuando este ticket esté
   cerrado.
4. **Flujo** (P4): `CLAUDE.md`.
5. **Regla del Project** (P3): el desarrollador desactiva "Pull request linked to issue" y
   se documenta.
6. **Verificación** en una sesión nueva: el revisor con un bloqueante sembrado y luego
   `/abrir-pr` real para cerrar este ticket (FR-016).
7. **Después del merge**: `/siguiente-ticket` sobre el issue #3 (SC-001, SC-004).

La historia P1 se implementa antes de cerrar el ticket, pero su prueba de punta a punta
ocurre al iniciar el issue #3. Probarla antes obligaría a iniciar un ticket con este aún
abierto.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| `dontAsk` niega también Read, Grep o Glob, o deja pasar otros comandos | Verificación explícita (quickstart §3); fallback con hook `PreToolUse` en el frontmatter (R3). |
| Las instrucciones de la skill no se siguen al pie de la letra | Instrucciones numeradas, criterios de parada explícitos y prueba real con el issue #3. |
| `/abrir-pr` toma un número de issue equivocado | Lo deduce de `spec.md` (`Issue: #N`) y lo confirma con el título del issue antes de publicar (FR-011). |
| La regla "Pull request linked to issue" sigue activa | La verificación del cierre de este ticket comprueba el estado tras crear el PR. |
| Reintentos duplican comentarios | Marcadores de comentario y consulta previa (R7). |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
