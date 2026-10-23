# Quickstart de validación: Automatización del ciclo en GitHub

Escenarios que prueban la spec de punta a punta. Para los detalles, ver
[contracts/](contracts/) y [data-model.md](data-model.md).

## Prerrequisitos

- Lo del issue #1: `GITHUB_PAT` visible y servidor MCP `github` conectado.
- Sesión de Claude Code reiniciada después de crear los archivos de `.claude/`, para que se
  carguen la skill, el comando y el subagente.

## 1. Las piezas cargan

1. En `/` aparecen `siguiente-ticket` y `abrir-pr`.
2. El subagente `revisor-codigo` aparece entre los agentes disponibles.

## 2. Regla del Project (US3 · FR-013, FR-014)

1. El desarrollador desactiva "Pull request linked to issue" en el Project
   (⋯ → Workflows) y confirma que "Item closed" sigue activa.
2. Se registra el resultado en el comentario de cierre del ticket.

## 3. Revisor acotado e independiente (US2 · FR-007, FR-008)

1. Delegar en `revisor-codigo` y pedirle que ejecute `git status` → **negado**.
2. Pedirle `git diff main..HEAD --stat` → **permitido**.
3. Pedirle que lea `specs/002-automatizacion-ciclo/spec.md` → **permitido**.
4. Si el paso 1 se permite o el 3 se niega: aplicar el fallback de
   [contracts/revisor-codigo.md](contracts/revisor-codigo.md) y repetir.

## 4. `/abrir-pr` se detiene ante un bloqueante (US2 · SC-003)

1. En una rama de prueba `999-prueba-revisor`, crear `specs/999-prueba-revisor/spec.md`
   con `Issue: #2` y un requisito ("el archivo `demo.txt` MUST decir 'hola'"). Agregar un
   `demo.txt` que diga otra cosa y hacer commit.
2. Ejecutar `/abrir-pr` → el revisor devuelve `BLOQUEADO` y el comando **no** publica la
   rama, no crea un PR y no comenta.
3. Volver a `002-automatizacion-ciclo` y borrar la rama de prueba sin publicarla.

## 5. Cierre de este ticket con `/abrir-pr` (US2, US3, US4 · FR-010, FR-016)

1. En `002-automatizacion-ciclo`, con todo commiteado, ejecutar `/abrir-pr`.
2. Se espera:
   - Veredicto `APROBADO`.
   - Rama publicada.
   - PR con `Closes #2`.
   - Issue en *In Review*.
   - Comentario con marcador "**PR abierto**", que incluye los ajustes de los puntos de
     control.
3. Ejecutar `/abrir-pr` otra vez → no duplica el PR ni el comentario (FR-012).
4. El desarrollador fusiona → el issue #2 queda cerrado y en *Done* sin intervención.

## 6. Inicio automático del siguiente ticket (US1 · SC-001, SC-004)

Ya en `main` con el merge:

1. Ejecutar `/siguiente-ticket` sin argumentos.
2. Se espera:
   - Elige el issue #3 (dependencia #1 cerrada) e informa por qué.
   - Lo mueve a *In Progress* y comenta el inicio.
   - Crea la rama `003-...`.
   - Genera `specs/003-.../spec.md` con `Issue: #3`.
   - Se detiene pidiendo revisión.

Este escenario cierra el ciclo: desde aquí ningún movimiento de estado es manual.
