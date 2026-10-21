# Quickstart de validación: Bootstrap del proceso

Escenarios ejecutables que prueban la spec de punta a punta. Para los detalles, ver
[contracts/](contracts/) y [data-model.md](data-model.md).

## Prerrequisitos

- `git`, `uv` 0.13 o superior, Claude Code.
- Variable de entorno de usuario `GITHUB_PAT`: PAT clásico con `repo` y `project`.
- Aplicación de Claude reiniciada por completo después de definir la variable.

## 1. Secretos fuera de alcance (US1 · FR-001 a FR-004 · SC-001, SC-002)

1. Crear `.env` y `config/.env` con un valor ficticio, por ejemplo `CLAVE_FICTICIA=valor-de-prueba`.
2. `git status --short`: no aparecen. `git check-ignore -v .env.example` no devuelve nada.
3. Pedir al asistente, en una sesión nueva:
   - Que lea `.env` → **negado**.
   - Que busque `CLAVE_FICTICIA` en el repositorio → `.env` **no aparece** en los resultados.
   - Que ejecute `cat .env`, `grep CLAVE .env`, `cp .env copia.txt` y `Get-Content .env` →
     **negados**.
   - Que edite `.env` → **negado**.
   - Que lea `.env.example` → **permitido**.
4. Barrer el historial en busca de tokens: `git log -p --all` no contiene `ghp_`, `gho_` ni
   `github_pat_`.
5. Borrar los archivos de prueba.

**Esperado**: el 100% de las vías probadas se niega; cero credenciales en el historial.

## 2. Convenciones al clonar (US2 · FR-005 a FR-009 · SC-003, SC-004)

1. Clonar el repositorio en un directorio temporal y abrir allí una sesión del asistente.
2. Preguntar: "¿Cuál es el umbral de disputa automática?" → responde $500.000, tomado de la
   constitución importada.
3. Ejecutar un comando de Spec Kit que imprima JSON, por ejemplo
   `/speckit-specify` en modo de prueba o el script `resolve_template.py` desde el asistente →
   **sin errores de codificación**.
4. Crear `CLAUDE.local.md` y `.claude/settings.local.json` → `git status` no los muestra.

## 3. Estructura base (US4 · FR-014 a FR-016 · SC-005)

1. Borrar `.venv` y ejecutar `uv sync` → termina sin errores en menos de 2 minutos.
2. `uv run python -c "import agente_disputas, core_bancario_mcp"` → sin errores.
3. `uv run pytest` → los 2 tests de humo pasan; termina con código 0.

## 4. Conexión con el Project (US3 · FR-010 a FR-013 · SC-006)

1. `.mcp.json` solo contiene `${GITHUB_PAT}` (inspección visual).
2. En la sesión, `/mcp` → el servidor `github` aparece conectado.
3. Pedir al asistente que mueva el issue #1 de *In Progress* a *In Review* y de vuelta a
   *In Progress* → ambos cambios son visibles en el Project.
4. Pedir al asistente que comente en el issue #1 el resultado de la verificación.

**Esperado**: los movimientos funcionan en el primer intento, y el comentario queda como
evidencia.

## 5. Trazabilidad (FR-017 · SC-007)

- `specs/001-bootstrap-proceso/` contiene `spec.md`, `plan.md` y `tasks.md`.
- El PR del ticket incluye `Closes #1`.
- El issue muestra el comentario de inicio, la verificación del MCP y el cierre por el PR.
