# Andino Dispute Agent

Agente de disputas de transacciones para Banco Andino (ficticio), con Claude Agent SDK y un
servidor MCP propio (`core-bancario`). Los principios del proyecto viven en la constitución,
que es la fuente única de verdad:

@.specify/memory/constitution.md

## Comandos

- `uv sync`: instala dependencias.
- `uv run pytest`: tests deterministas (siempre en verde).
- `uv run pytest -m e2e`: tests de escenario (requieren `ANTHROPIC_API_KEY`).

## Flujo por ticket (definición de hecho)

1. `/siguiente-ticket [N]`: mueve el issue a *In Progress*, crea la rama `NNN-slug` y
   genera la spec. **Control 1**: revisar `spec.md` (`/speckit-clarify` si es ambigua).
2. `/speckit-plan`. **Control 2**: revisar `plan.md` antes de `/speckit-tasks`.
3. `/speckit-tasks` y `/speckit-analyze`. **Control 3**: revisar el análisis antes de
   `/speckit-implement` (y `/speckit-converge` si quedan brechas).
4. `/abrir-pr`: revisión independiente (`revisor-codigo`), PR con `Closes #N`, issue a
   *In Review* y comentario con los ajustes de cada control.
5. El merge lo hace el desarrollador y es la aprobación final; el Project pasa el issue a
   *Done*. No se escribe en `src/` sin `spec.md`, `plan.md` y `tasks.md`.

## Convenciones

- Tests junto al código (`test_*.py` en la misma carpeta que el módulo).
- Solo datos ficticios; nunca leas ni edites `.env*`.
- Preferencias personales en `CLAUDE.local.md` o `.claude/settings.local.json` (no se
  versionan).
