# Andino Dispute Agent

Agente de disputas de transacciones para Banco Andino (ficticio), con Claude Agent SDK y un
servidor MCP propio (`core-bancario`). Los principios del proyecto viven en la constitución,
que es la fuente única de verdad:

@.specify/memory/constitution.md

## Comandos

- `uv sync`: instala dependencias.
- `uv run pytest`: tests deterministas (siempre en verde).
- `uv run pytest -m e2e`: tests de escenario (requieren `ANTHROPIC_API_KEY`).

## Flujo por ticket

1. Cada ticket nace de un issue de GitHub y se especifica con `/speckit-specify`.
2. Puntos de control humanos: revisar `spec.md` (y `/speckit-clarify` si es ambigua),
   revisar `plan.md` antes de `/speckit-tasks`, y revisar `/speckit-analyze` antes de
   `/speckit-implement`.
3. No se escribe en `src/` sin `spec.md`, `plan.md` y `tasks.md` en `specs/<rama>/`.
4. El pull request referencia y cierra su issue (`Closes #N`).

## Convenciones

- Tests junto al código (`test_*.py` en la misma carpeta que el módulo).
- Solo datos ficticios; nunca leas ni edites `.env*`.
- Preferencias personales en `CLAUDE.local.md` o `.claude/settings.local.json` (no se
  versionan).
