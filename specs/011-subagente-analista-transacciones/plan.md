# Implementation Plan: Subagente `analista-transacciones`

**Branch**: `011-subagente-analista-transacciones` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-subagente-analista-transacciones/spec.md` (issue #11)

## Summary

- **Subagente** (`analista.py`, nuevo): `AgentDefinition` con una sola herramienta
  (`consultar_transacciones`), instrucciones armadas con la política del banco y resultado
  estructurado (`<analisis>`).
- **Control de delegación** (`controles.py`): `PreToolUse` sobre la herramienta de delegación
  que exige el subagente correcto, cliente verificado y un bloque `<contexto>` completo con el
  cliente verificado; falla cerrado. Las consultas del subagente siguen pasando por los
  controles del #9 (se comprueba con la API).
- **Configuración**: el principal gana solo la herramienta de delegación; sin política, ni
  subagente ni delegación.
- **Prompt v5**: cuándo y cómo delegar y cómo usar la clasificación.
- **Ajustes heredados del #10**.

Decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: `claude-agent-sdk` 0.2.168 (`AgentDefinition`,
`ClaudeAgentOptions.agents`, hooks con `agent_id`); `core_bancario_mcp.repositorio.Politica`

**Storage**: ninguno

**Testing**: `pytest` determinista (definición, prompt, validación del bloque, control de
delegación, opciones); sonda y escenario `e2e` con la API para la delegación real y la
cobertura de los controles sobre el subagente

**Target Platform**: la misma de los tickets anteriores

**Project Type**: aplicación de línea de comandos dentro del proyecto `uv`

**Performance Goals**: `maxTurns=8` en el subagente como salvaguarda de costo

**Constraints**:
- El subagente tiene exactamente una herramienta.
- El principal solo gana la herramienta de delegación; `setting_sources=[]` y
  `strict_mcp_config` siguen igual.
- El bloque `<contexto>` se valida sin interpretar texto libre.
- La clasificación nunca reemplaza los controles.

**Scale/Scope**: 1 módulo nuevo con su test, cambios en `controles.py`, `configuracion.py`,
`prompts.py` y sus tests, 1 escenario `e2e`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | Regla 1: delegación solo con cliente verificado y para ese cliente; consultas del subagente con los controles del #9. Regla 2: el subagente no puede disputar; el principal sigue con el control del umbral. Reglas 3 a 5 sin cambios. | ✅ |
| II. Garantías deterministas | Control `PreToolUse` sobre la delegación (falla cerrado); controles del #9 sobre las consultas del subagente (verificado con la API); clasificación declarada como orientativa (instrucción + verificación con la API). | ✅ |
| III. Datos ficticios y cero credenciales | Solo `CLI-00N`/`TRX-00N`; razones con nombres de campo, nunca valores ni datos de otros clientes. | ✅ |
| IV. Spec-first | Spec aprobada (commit `92cccc2`); plan y tareas antes de `src/`. | ✅ |
| V. Contrato de herramientas | El subagente usa `consultar_transacciones` con su contrato; el resultado estructurado del subagente es interno al agente. | ✅ |
| VI. Tests en dos niveles | Deterministas junto a cada módulo; escenario `e2e` de delegación con mensaje distinto de los ejemplos del prompt. | ✅ |
| VII. Simplicidad | Un módulo pequeño (`analista.py`) y un callback más en `controles.py`; se reutilizan los controles existentes. | ✅ |

**Resultado**: todos los gates pasan. **Re-evaluación tras la fase 1**: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/011-subagente-analista-transacciones/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── subagente.md
│   └── heredados-010.md
├── checklists/requirements.md
└── tasks.md                     # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
src/agente_disputas/
├── analista.py                  # nuevo: definición, prompt y lectura del <contexto>
├── test_analista.py             # nuevo
├── controles.py                 # mod: antes_de_delegar, heredado (c)
├── test_controles.py            # mod
├── configuracion.py             # mod: agents, herramienta de delegación
├── test_configuracion.py        # mod
├── prompts.py                   # mod: v5
└── test_prompts.py              # mod
tests/escenarios/test_delegacion_e2e.py            # nuevo, marcado e2e
specs/010-escalamiento-criterio-solicitudes/tasks.md  # mod: heredado (a)
```

**Structure Decision**: la definición del subagente y la lectura del bloque viven juntas en
`analista.py` (un mismo contrato para el control y para las instrucciones); el control usa
`leer_contexto` desde `controles.py` ([research.md R2, R4](research.md)).

## Orden de implementación

1. **Sonda** con la API (research R1): nombre y entrada de la herramienta de delegación,
   `agent_id` en los hooks del subagente, `UserPromptSubmit`.
2. **Heredados del #10** (US5).
3. **`analista.py`** (US1, US4): definición, prompt con la política y `leer_contexto`, test
   primero.
4. **Control de delegación** (US1, US3) y cobertura de consultas con `agent_id`.
5. **Configuración** (US2) y **prompt v5** (FR-009).
6. **Escenario e2e** y **verificación** (quickstart), luego `/abrir-pr`.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| La herramienta de delegación tiene otro nombre o entrada | Sonda primero; matcher `Agent|Task`; constante única `HERRAMIENTA_DELEGAR` |
| Los hooks no reciben las llamadas del subagente | La sonda lo detecta antes de implementar; si no llegan, la regla 1 del subagente no está garantizada y se detiene el ticket para decidir |
| La delegación dispara `UserPromptSubmit` y vacía pendientes | `al_recibir_mensaje` ignora entradas con `agent_id` (test) |
| El subagente clasifica mal | Clasificación orientativa; los controles y el core deciden (SC-005) |
| Costo y latencia extra | `maxTurns=8`; el prompt pide delegar solo con cobros por analizar |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
