# Implementation Plan: Datos ficticios, contrato de errores e inyección de fallas

**Branch**: `004-datos-errores-fallas` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-datos-errores-fallas/spec.md` (issue #4)

## Summary

Cimientos del servidor `core-bancario` en el paquete `core_bancario_mcp`:

- **Contrato de errores** (`errores.py`), con `reintentable` derivado del tipo.
- **Datos ficticios en JSON**, con fechas relativas.
- **Repositorio** (`repositorio.py`): carga, valida y consulta transacciones por id; el
  agente lo reutilizará.
- **Inyección de fallas por variable de entorno** (`fallas.py`).
- **Servidor FastMCP** (`servidor.py`, `__main__.py`), registrado en `.mcp.json`.

Más los tres ajustes heredados del issue #3. Decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: `mcp[cli]` 1.30.0 (`FastMCP`), ya declarado; solo biblioteca
estándar para datos, errores y fallas

**Storage**: archivos JSON versionados en `src/core_bancario_mcp/datos/`; estado mutable en
memoria del proceso del servidor

**Testing**: `pytest`, con tests junto a cada módulo (`test_*.py`) y "hoy" inyectado; un
test de arranque del servidor por stdio

**Target Platform**: Windows, Linux y macOS; Claude Code lanza el servidor por stdio

**Project Type**: biblioteca y servidor MCP dentro del proyecto `uv`

**Performance Goals**: el servidor arranca en menos de 5 s (SC-005)

**Constraints**:
- Solo datos ficticios: el hook `bloquear_pii` y el CI vigilan.
- Nada bajo `src/` sin spec, plan y tareas: lo vigila el hook `exigir_spec`.
- Tests sin reloj real.

**Scale/Scope**: 5 módulos con sus tests, 4 archivos de datos, cambios en `.mcp.json`, en la
rule de MCP y en `bloquear_pii`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | Prepara los datos de las reglas (umbral de $500.000 exacto, exterior con más de 90 días, tarjeta bloqueada) y el monto consultable en el core para la regla 2. | ✅ |
| II. Garantías deterministas | `reintentable` derivado del tipo (imposible por diseño). La consulta del monto para el hook es directa al repositorio, sin depender del modelo ni del transporte. Los datos inválidos impiden el arranque. | ✅ |
| III. Datos ficticios | Tarjetas solo con `ultimos4`; documentos validados contra `CC-FIC-NNNN` al cargar; el hook y el CI revisan los JSON. | ✅ |
| IV. Spec-first | Spec aprobada; plan y tareas antes de escribir en `src/` (el hook lo exige). | ✅ |
| V. Contrato de herramientas | `errores.py` implementa exactamente el contrato, con los 4 tipos; búsqueda vacía = éxito. | ✅ |
| VI. Tests junto al código | Un `test_*.py` por módulo, con "hoy" inyectado. | ✅ |
| VII. Simplicidad | JSON y biblioteca estándar; sin base de datos ni dependencias nuevas. | ✅ |

**Resultado**: todos los gates pasan. **Re-evaluación tras la fase 1**: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/004-datos-errores-fallas/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── errores.md
│   ├── datos.md
│   ├── fallas.md
│   ├── repositorio.md
│   └── servidor.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/core_bancario_mcp/
├── __init__.py                 # existente
├── __main__.py                 # nuevo: arranca el servidor
├── errores.py                  # nuevo
├── test_errores.py             # nuevo
├── repositorio.py              # nuevo
├── test_repositorio.py         # nuevo
├── fallas.py                   # nuevo
├── test_fallas.py              # nuevo
├── servidor.py                 # nuevo
├── test_servidor.py            # nuevo
└── datos/
    ├── clientes.json           # nuevo
    ├── tarjetas.json           # nuevo
    ├── transacciones.json      # nuevo
    └── politicas.json          # nuevo
.mcp.json                                    # mod: servidor core-bancario
.claude/rules/herramientas-mcp.md            # mod: cita el contrato de errores
plugins/andino-guardrails/hooks/bloquear_pii.py      # mod: /dev/null en --diff
plugins/andino-guardrails/hooks/test_bloquear_pii.py # mod: tests 4-6-5 y /dev/null
```

**Structure Decision**: un módulo por responsabilidad dentro de `core_bancario_mcp`, con sus
tests al lado; los datos dentro del paquete para cargarlos con `importlib.resources`
([research.md R1 y R3](research.md)).

## Orden de implementación

1. **Errores** (US1): tests y luego `errores.py`.
2. **Datos y repositorio** (US2, US4): JSON, tests con "hoy" fijo y `repositorio.py`.
3. **Fallas** (US3): tests y `fallas.py`.
4. **Servidor** (US5): `servidor.py`, `__main__.py`, test de arranque y `.mcp.json`.
5. **Ajustes heredados** (US6).
6. **Verificación**: sesión nueva con `core-bancario` conectado, y luego `/abrir-pr`.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Un JSON de datos dispara el hook `bloquear_pii` | Documentos `CC-FIC-NNNN`, tarjetas solo con `ultimos4` y montos sin palabra de documento: el diseño no tiene forma real. Si bloquea, se corrige el dato, nunca el hook. |
| El agente y el servidor ven estado distinto (procesos separados) | El hook solo usa datos inmutables (monto, titular). Límite declarado en R7. |
| El arranque del servidor en el test cuelga | El test usa el cliente stdio de `mcp` con tiempo límite. |
| Bloqueo de `.venv` en Windows al lanzar con `uv run` | `--no-sync` en `.mcp.json` (R8). |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
