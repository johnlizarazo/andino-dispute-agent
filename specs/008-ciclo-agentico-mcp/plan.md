# Implementation Plan: Ciclo agéntico y conexión al MCP

**Branch**: `008-ciclo-agentico-mcp` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-ciclo-agentico-mcp/spec.md` (issue #8)

## Summary

El primer código del paquete `agente_disputas`:

- **Configuración** (`configuracion.py`): opciones del `ClaudeSDKClient` con solo las 6
  herramientas del core, sin herramientas ni settings del entorno, sin permisos interactivos,
  `max_turns` como salvaguarda, modelo configurable y credencial exigida.
- **Ciclo** (`ciclo.py`): procesa los mensajes de cada turno hasta el resultado y lo clasifica
  por razón de parada y subtipo (completado, salvaguarda, falla del servicio, error).
- **Prompt** (`prompts.py`): prompt de sistema inicial versionado.
- **CLI** (`cli.py`, `__main__.py`): conversación turno a turno en la terminal.
- **Ajustes heredados del #7**.

Decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: `claude-agent-sdk` 0.2.168 (ya declarado); el servidor
`core_bancario_mcp` del mismo proyecto

**Storage**: ninguno; la conversación vive en la sesión del cliente

**Testing**: `pytest`; deterministas sin API (opciones, clasificación del turno con mensajes
simulados, CLI con un cliente falso); escenarios `e2e` en `tests/escenarios/` con
`ANTHROPIC_API_KEY`

**Target Platform**: terminal en Windows, Linux y macOS. `uv.lock` incluye el SDK para
Windows, Linux (x86_64 y aarch64) y macOS, cada uno con su CLI empaquetado; el CI ya corre los
tests deterministas en `ubuntu-latest`. La verificación manual en Linux queda en el
quickstart §3b.

**Project Type**: aplicación de línea de comandos dentro del proyecto `uv`

**Performance Goals**: primera respuesta en menos de 30 s (SC-005)

**Constraints**:
- Solo `mcp__core-bancario__*` (6 herramientas); `tools=[]`, `dontAsk`, `strict_mcp_config`,
  `setting_sources=[]`.
- La clave solo desde `ANTHROPIC_API_KEY`, nunca impresa.
- Ningún control del ciclo por contadores o palabras; `max_turns` solo como salvaguarda.

**Scale/Scope**: 4 módulos nuevos con sus tests, 1 escenario `e2e`, ajustes en
`bloqueo_escalamiento.py` y su test, y en el plan del #7

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | El prompt orienta las 5 reglas; su garantía determinista (hooks de reglas 1 y 2, hook `Stop`) llega en #9 y #10, que se enganchan a estas mismas opciones. | ✅ |
| II. Garantías deterministas | Herramientas limitadas por configuración (determinista, con test). Ciclo por razón de parada, por diseño. Reintentos por instrucción + escenario, justificado en la spec (no es regla de negocio). | ✅ |
| III. Datos ficticios y cero credenciales | `ANTHROPIC_API_KEY` solo del entorno, nunca impresa ni versionada; sin `.env` en tiempo de ejecución; mensajes de tests ficticios. | ✅ |
| IV. Spec-first | Spec aprobada (commit `a91c797`); plan y tareas antes de `src/`. | ✅ |
| V. Contrato de herramientas | El prompt explica cómo actuar según `tipo` y `reintentable`; no cambia el contrato del core. | ✅ |
| VI. Tests en dos niveles | Deterministas junto a cada módulo; escenario `e2e` en `tests/escenarios/` con mensajes distintos de los ejemplos del prompt. | ✅ |
| VII. Simplicidad | El SDK ejecuta el ciclo de herramientas; el código propio solo configura, clasifica y conversa. | ✅ |

**Resultado**: todos los gates pasan. **Re-evaluación tras la fase 1**: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/008-ciclo-agentico-mcp/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── configuracion.md
│   ├── ciclo-y-cli.md
│   └── heredados-007.md
├── checklists/requirements.md
└── tasks.md                     # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
src/agente_disputas/
├── prompts.py                   # nuevo
├── test_prompts.py              # nuevo
├── configuracion.py             # nuevo
├── test_configuracion.py        # nuevo
├── ciclo.py                     # nuevo
├── test_ciclo.py                # nuevo
├── cli.py                       # nuevo
├── test_cli.py                  # nuevo
└── __main__.py                  # nuevo
tests/escenarios/
├── __init__.py                  # nuevo (si hace falta para pytest)
└── test_conversacion_e2e.py     # nuevo, marcado e2e
src/core_bancario_mcp/bloqueo_escalamiento.py      # mod: heredados (a) y (c)
src/core_bancario_mcp/test_bloqueo_escalamiento.py # mod: heredados (a) y (b)
specs/007-bloqueo-escalamiento/plan.md             # mod: heredado (d)
```

**Structure Decision**: módulos pequeños y puros alrededor del SDK; la E/S (SDK, terminal)
queda en `cli.py` ([research.md R1](research.md)).

## Orden de implementación

1. **Heredados del #7** (US5).
2. **Prompt** y **configuración** (US3): tests de las opciones sin API.
3. **Ciclo** (US2): tests con mensajes simulados.
4. **CLI** (US1, US4): tests con un cliente falso; `__main__.py`.
5. **Escenario e2e** (US4): falla transitoria inyectada.
6. **Verificación**: conversación real en la terminal (quickstart), y luego `/abrir-pr`.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El CLI subyacente del SDK no está disponible en la máquina | Verificado: el paquete trae el CLI empaquetado (`claude_agent_sdk/_bundled`). Igual se captura `CLINotFoundError` con mensaje claro. |
| El SDK cambia nombres de campos | Versión fijada por `uv.lock`; la clasificación se prueba con mensajes construidos con las clases reales del SDK. |
| Falta `ANTHROPIC_API_KEY` en la sesión | La CLI lo informa; los tests `e2e` se saltan sin la variable. |
| Settings o hooks del desarrollador se cuelan en el agente | `setting_sources=[]` y `strict_mcp_config=True`, verificados en el test de opciones. |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
