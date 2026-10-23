# Implementation Plan: Hooks del SDK para R1 y R2

**Branch**: `009-hooks-sdk-r1-r2` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/009-hooks-sdk-r1-r2/spec.md` (issue #9)

## Summary

Las reglas 1 y 2 pasan de "imposible por diseño" (herramientas deshabilitadas en el #8) a
"garantizadas por hook":

- **Controles** (`controles.py`, nuevo): un hook `PostToolUse` sobre `verificar_identidad`
  registra el cliente verificado en el estado de la conversación; un hook `PreToolUse` sobre
  `consultar_transacciones`, `iniciar_disputa` y `bloquear_tarjeta` niega sin identidad, sobre
  productos de otro cliente o con una disputa sobre $500.000 (monto leído del repositorio del
  core). Falla cerrado ante cualquier error.
- **Configuración**: registra los hooks por nombre completo y habilita las 6 herramientas.
- **Prompt v3**: sin "Disponibilidad actual"; orienta qué hacer cuando un control niega.
- **Ajustes heredados del #8**.

Decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: `claude-agent-sdk` 0.2.168 (`HookMatcher`, hooks `PreToolUse` y
`PostToolUse`); `core_bancario_mcp.repositorio` (`Repositorio`, `Politica`) y
`core_bancario_mcp.fallas.InyectorFallas`, reutilizados en el proceso del agente

**Storage**: ninguno; `EstadoSesion` en memoria por conversación

**Testing**: `pytest`; los callbacks se prueban sin API llamándolos con entradas construidas a
mano; un escenario `e2e` sin prompt de sistema en `tests/escenarios/`

**Target Platform**: la misma del #8 (terminal en Windows, Linux y macOS)

**Project Type**: aplicación de línea de comandos dentro del proyecto `uv`

**Performance Goals**: los controles son consultas en memoria (microsegundos); no cambian la
meta de primera respuesta del #8

**Constraints**:
- Matchers por nombre completo `mcp__core-bancario__...` (FR-008).
- Los hooks no leen el prompt (FR-009).
- Falla cerrada implementada en nuestro código, no delegada al CLI (research R2).
- El monto y el titular salen del repositorio por `transaccion_id`, nunca de otro argumento.

**Scale/Scope**: 1 módulo nuevo con su test, cambios en `configuracion.py`, `prompts.py`,
`ciclo.py`, `cli.py` y sus tests, 1 escenario `e2e`, el ajuste (a) en `bloqueo_escalamiento.py`
y su test, la regla de herramientas y el texto de T007 del #8

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | Regla 1: identidad y titularidad por hook (`SIN_IDENTIDAD`, `CLIENTE_DISTINTO`, `TRANSACCION_NO_CONFIRMADA`); exentas sin matcher; bloquear exige identidad. Regla 2: umbral por hook con el monto del repositorio, 500000 inclusive. Reglas 3 y 5: el core (sin cambios). Regla 4: prompt + escenarios (sin cambios). | ✅ |
| II. Garantías deterministas | Reglas 1 y 2 con `PreToolUse` que niega con razón y falla cerrado (try/except, lista blanca, falla inyectable `control_transaccion`). Nivel declarado en la spec (Assumptions). Test sin prompt. El `Stop` queda en el #10. | ✅ |
| III. Datos ficticios y cero credenciales | Solo `TRX-00N`/`CLI-00N` ficticios en tests; razones sin datos de otros clientes; sin credenciales nuevas. | ✅ |
| IV. Spec-first | Spec aprobada (commit `9637b0a`); plan y tareas antes de `src/`. | ✅ |
| V. Contrato de herramientas | El core no cambia su contrato; el ajuste (a) responde con `PARAMETRO_INVALIDO` del contrato. La negación del hook no es una respuesta del core: es la razón de permisos del SDK. | ✅ |
| VI. Tests en dos niveles | `test_controles.py` junto al módulo, sin API; escenario `e2e` sin prompt con mensaje distinto de los ejemplos del prompt. | ✅ |
| VII. Simplicidad | Un módulo y dos callbacks; reutiliza `Repositorio`, `Politica` e `InyectorFallas` en lugar de duplicarlos. | ✅ |

**Resultado**: todos los gates pasan. **Re-evaluación tras la fase 1**: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/009-hooks-sdk-r1-r2/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── controles.md
│   └── heredados-008.md
├── checklists/requirements.md
└── tasks.md                     # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
src/agente_disputas/
├── controles.py                 # nuevo: EstadoSesion, Controles, leer_respuesta, hooks
├── test_controles.py            # nuevo
├── configuracion.py             # mod: hooks, 6 herramientas habilitadas
├── test_configuracion.py        # mod: matchers, sin prompt, estado por conversación
├── prompts.py                   # mod: v3, líneas largas
├── test_prompts.py              # mod: versión y sin "Disponibilidad actual"
├── ciclo.py                     # mod: AsyncIterable[Message]
├── cli.py                       # mod: líneas largas
└── test_cli.py                  # mod: main con Ctrl+C y CLINotFoundError
tests/escenarios/test_conversacion_e2e.py           # mod: escenario sin prompt
src/core_bancario_mcp/bloqueo_escalamiento.py      # mod: heredado (a)
src/core_bancario_mcp/test_bloqueo_escalamiento.py # mod: heredado (a), test invertido
.claude/rules/herramientas-mcp.md                  # mod: escalar sin cliente no lleva transacciones
specs/008-ciclo-agentico-mcp/tasks.md              # mod: heredado (c)
```

**Structure Decision**: los controles en un módulo propio del agente, puro sobre entradas y
estado, con los datos inyectados; `configuracion.py` solo los registra
([research.md R6, R7](research.md)).

## Orden de implementación

1. **Heredados del #8** (US5): (a) en el core con su test invertido; (b) a (e).
2. **Controles** (US1–US3), test primero: estado y registro de la verificación; identidad;
   titularidad; umbral; falla cerrada.
3. **Configuración** (US4): hooks, 6 herramientas, test sin prompt y estado por conversación.
4. **Prompt v3** (FR-010).
5. **Escenario e2e sin prompt**.
6. **Verificación**: quickstart §3 con la API (incluye confirmar la forma de `tool_response`),
   y luego `/abrir-pr`.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| La forma de `tool_response` del `PostToolUse` no coincide con lo esperado y nunca se registra al cliente | Falla cerrada (nada se autoriza de más); `leer_respuesta` acepta las formas conocidas; quickstart §3b lo confirma con la API y se ajusta antes del PR |
| Un error del hook deja pasar la herramienta (comportamiento del CLI) | try/except en cada callback con negación; tests que fuerzan excepciones |
| Tiempo de espera del hook agotado | Controles en memoria; `timeout=10` |
| El modelo pide `iniciar_disputa` repetidamente tras una negación | La razón indica qué hacer (verificar o escalar); `max_turns` sigue de salvaguarda; la obligación de escalar es del #10 |
| Agente y core cargan datos distintos | Ambos usan el mismo paquete de datos; monto y titular son inmutables (spec, Assumptions) |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
