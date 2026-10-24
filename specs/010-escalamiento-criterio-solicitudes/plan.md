# Implementation Plan: Escalamiento con criterio y solicitudes múltiples

**Branch**: `010-escalamiento-criterio-solicitudes` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-escalamiento-criterio-solicitudes/spec.md` (issue #10)

## Summary

- **Escalamiento pendiente por hook** (`controles.py`): la negación por umbral del control y
  los rechazos del core (`FUERA_DE_POLITICA`, `REQUIERE_ANALISTA`) crean pendientes; un hook
  `Stop` impide terminar el turno mientras haya pendientes, hasta 2 veces; un escalamiento
  exitoso con la transacción y la causa los limpia; un hook `UserPromptSubmit` los vacía al
  llegar un nuevo mensaje. Los pendientes no bloquean otras operaciones.
- **Falla visible** (`cli.py`): si un turno termina con pendientes, la línea de comandos avisa.
- **Prompt v4** y descripción de `escalar_a_analista`: persona a pedido, criterio, varios
  asuntos y 4 ejemplos en `<ejemplos>` con datos que no existen en el core ni en los tests.
- **Ajustes heredados del #9**.

Decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: `claude-agent-sdk` 0.2.168 (hooks `Stop`, `UserPromptSubmit`,
`PostToolUse`); `core_bancario_mcp` (`lista_de_ids`, causas de escalamiento)

**Storage**: ninguno; `EstadoSesion` en memoria por conversación

**Testing**: `pytest` determinista (callbacks llamados con entradas construidas a mano, CLI con
cliente falso, prompt leído como texto); validación manual con la API (quickstart §3). Los
escenarios automáticos del #10 se escriben en el #13.

**Target Platform**: la misma del #8 y el #9

**Project Type**: aplicación de línea de comandos dentro del proyecto `uv`

**Performance Goals**: sin cambios; el tope de 2 cierres limita el costo extra de un turno

**Constraints**:
- La petición de una persona no se detecta con palabras ni con hooks (FR-010).
- Los pendientes no se consultan en `PreToolUse` (FR-006).
- Ejemplos del prompt sin datos del core ni mensajes de los tests (principio VI), con test.
- Solo se escalan pendientes con un escalamiento que incluye la transacción y la causa.

**Scale/Scope**: cambios en `controles.py`, `configuracion.py`, `cli.py`, `prompts.py`,
`__init__.py`, `bloqueo_escalamiento.py` y sus tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | Regla 4: escalar de inmediato a pedido (prompt + descripción + ejemplos). Reglas 2 y 5: lo que no se inicia se escala (hook `Stop`). Reglas 1 y 3: sin cambios; el pendiente no bloquea el bloqueo. | ✅ |
| II. Garantías deterministas | Escalar tras umbral o política: hook `Stop` sobre el estado con tope de 2 (exigido literalmente). Regla 4: instrucción + ejemplos positivos y negativos, sin palabras clave; verificada por escenario (manual aquí, automática en el #13). Niveles declarados en la spec. | ✅ |
| III. Datos ficticios y cero credenciales | Ejemplos del prompt con datos inventados que no están en el core; razones sin montos ni datos de otros clientes; sin credenciales nuevas. | ✅ |
| IV. Spec-first | Spec aprobada (commit `f0b1fc1`); plan y tareas antes de `src/`. | ✅ |
| V. Contrato de herramientas | Pendientes por `codigo` del contrato del core, no por texto; la descripción de `escalar_a_analista` dice cuándo usarla y cuándo no. | ✅ |
| VI. Tests en dos niveles | Deterministas junto a cada módulo; test que garantiza que los ejemplos del prompt no comparten datos con los tests de escenario. | ✅ |
| VII. Simplicidad | Se amplían los `Controles` existentes (dos campos de estado y cuatro callbacks); se reutiliza `lista_de_ids` del core. | ✅ |

**Falla abierta justificada**: una excepción en el hook `Stop` deja terminar el turno (no
autoriza ninguna operación; bloquear por un error podría forzar un ciclo). El pendiente queda
y la línea de comandos muestra el aviso, así que la falla es visible (research R4).

**Resultado**: todos los gates pasan. **Re-evaluación tras la fase 1**: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/010-escalamiento-criterio-solicitudes/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── escalamiento-pendiente.md
│   ├── prompt-y-descripcion.md
│   └── heredados-009.md
├── checklists/requirements.md
└── tasks.md                     # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
src/agente_disputas/
├── controles.py                 # mod: pendientes, 4 callbacks, heredados (a)(b)(c)
├── test_controles.py            # mod
├── configuracion.py             # mod: heredado (d)
├── test_configuracion.py        # mod: hooks Stop/UserPromptSubmit/PostToolUse nuevos
├── cli.py                       # mod: aviso de escalamiento pendiente
├── test_cli.py                  # mod
├── prompts.py                   # mod: v4 con <ejemplos>
├── test_prompts.py              # mod: ejemplos y separación de datos
└── __init__.py                  # mod: heredado (e)
src/core_bancario_mcp/bloqueo_escalamiento.py      # mod: lista_de_ids pública, descripción
src/core_bancario_mcp/test_bloqueo_escalamiento.py # mod: descripción
```

**Structure Decision**: todo el estado y los hooks siguen en `controles.py`; la interfaz solo
lee los pendientes para avisar ([research.md R3, R4](research.md)).

## Orden de implementación

1. **Heredados del #9** (US6).
2. **Pendientes** (US1, US2), test primero: creación por umbral y por core, limpieza por
   escalamiento y por mensaje, `Stop` con tope, mensaje de ejemplo.
3. **Registro de hooks** y **aviso en la CLI** (US1).
4. **Descripción de `escalar_a_analista`** y **prompt v4** con ejemplos y test de separación
   (US3 a US5).
5. **Verificación**: suite determinista, e2e existentes y validación manual (quickstart §3), y
   luego `/abrir-pr`.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El `Stop` bloquea y el modelo no escala (ciclo) | Tope de 2 por turno; aviso visible al terminar |
| El modelo escala con otra causa o sin la transacción | La razón del `Stop` nombra transacción y causa; el pendiente solo se limpia con ambas |
| `UserPromptSubmit` no se dispara en algún flujo del SDK | Test de registro; la validación manual (e) confirma el reinicio entre mensajes |
| Los ejemplos del prompt se parecen a los tests del #13 | Test de separación de datos; el #13 debe escribir mensajes nuevos y el test lo comprobará |
| El prompt más largo cambia el comportamiento de los e2e existentes | Correr `pytest -m e2e` en la verificación |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
