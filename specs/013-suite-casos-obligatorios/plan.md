# Implementation Plan: Suite de casos obligatorios y README

**Branch**: `013-suite-casos-obligatorios` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/013-suite-casos-obligatorios/spec.md` (issue #13)

## Summary

- **Registro de operaciones** (`tests/escenarios/registro.py`, nuevo): conversa con el agente
  real y arma, con funciones puras probadas sin API, la lista de llamadas del agente principal
  con argumentos, respuesta del core y negación del control, más los pendientes de escalar.
- **Suite** (`tests/escenarios/test_casos_obligatorios.py`, nuevo): un test `e2e` por caso
  obligatorio, con las comprobaciones de [contracts/casos.md](contracts/casos.md). Los
  mensajes viven en `tests/escenarios/casos.py`.
- **Mensajes fuera del prompt** (`tests/escenarios/test_mensajes.py`, nuevo, determinista).
- **Consolidación**: los tests de falla transitoria de `test_conversacion_e2e.py` pasan a la
  suite (caso 5).
- **README**: inicio rápido para Windows y Linux/macOS, escenarios y tabla de casos.

No cambia nada en `src/`. Decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: `claude-agent-sdk` 0.2.168 (`ClaudeSDKClient`, bloques de
mensaje), `agente_disputas` (`crear_opciones`, `Controles`, `leer_respuesta`,
`procesar_turno`, `PROMPT_SISTEMA`), `core_bancario_mcp.repositorio.Repositorio`

**Storage**: ninguno

**Testing**: `pytest`; deterministas (`test_registro.py`, `test_mensajes.py`) y escenarios
`e2e` (`test_casos_obligatorios.py`)

**Target Platform**: Windows y Linux/macOS (README); misma ejecución que los tickets
anteriores

**Project Type**: tests y documentación del proyecto `uv`

**Performance Goals**: suite completa en menos de 10 minutos (SC-005); un turno por caso
(dos en el caso 5)

**Constraints**:
- Ninguna comprobación sobre el texto de la respuesta (FR-003).
- Datos de verificación leídos del core en tiempo de ejecución (FR-012).
- Sin cambios en el agente, el prompt, los controles ni el core.

**Scale/Scope**: 4 archivos nuevos en `tests/escenarios/`, 1 modificado
(`test_conversacion_e2e.py`), README

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | Sin cambios; la suite las verifica de punta a punta (reglas 1, 2, 4 y 5 y el bloqueo de la regla 3 en el caso 1). | ✅ |
| II. Garantías deterministas | No hay regla nueva. Los casos que dependen de instrucciones (2, 3, 5) se verifican con escenarios, como pide el principio; el umbral y la política se verifican contra el registro de operaciones y los pendientes del hook `Stop`. | ✅ |
| III. Datos ficticios y cero credenciales | Solo `CLI-00N`, `TRX-00N`, `CC-FIC-NNNN` y últimos 4; datos de verificación leídos del core; credencial solo del entorno, nunca en el README. | ✅ |
| IV. Spec-first | Spec aprobada (commit en la rama); plan y tareas antes de escribir tests. | ✅ |
| V. Contrato de herramientas | El registro lee las respuestas con el contrato `ok`/`datos`/`error`. | ✅ |
| VI. Tests en dos niveles | Escenarios `e2e` en `tests/escenarios/` con mensajes distintos del prompt (y un test determinista que lo vigila); ayudantes con su test determinista junto a ellos. | ✅ |
| VII. Simplicidad y trazabilidad | Un ayudante, un archivo de casos y un archivo de suite; se eliminan duplicados. | ✅ |

**Resultado**: todos los gates pasan. **Re-evaluación tras la fase 1**: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/013-suite-casos-obligatorios/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/casos.md
├── checklists/requirements.md
└── tasks.md                     # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
tests/escenarios/
├── registro.py                  # nuevo: Llamada, Registro, armar_registro, conversar
├── test_registro.py             # nuevo, determinista
├── casos.py                     # nuevo: mensajes de los seis casos
├── test_mensajes.py             # nuevo, determinista
├── test_casos_obligatorios.py   # nuevo, e2e: seis tests
└── test_conversacion_e2e.py     # mod: se quitan los dos tests de falla transitoria
README.md                        # mod: inicio rápido, escenarios, tabla de casos
```

**Structure Decision**: los ayudantes viven junto a los escenarios que los usan, con su test
al lado (convención de tests); `casos.py` separa los mensajes para compararlos con el prompt
sin importar un módulo de tests ([research.md R1, R2, R4](research.md)).

## Orden de implementación

1. **`registro.py`** con `test_registro.py` primero (armado del registro con mensajes
   construidos a mano: orden, emparejamiento, negaciones, respuestas ilegibles, llamadas del
   subagente excluidas).
2. **`casos.py`** y **`test_mensajes.py`** (test primero).
3. **Suite**: los seis casos según el contrato; quitar los duplicados de
   `test_conversacion_e2e.py`.
4. **README**.
5. **Verificación**: `uv run pytest`, la suite con la credencial (la corre el desarrollador si
   la clave no está en el entorno de Claude Code) y la prueba de 5 minutos con el README.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El modelo resuelve un caso por un camino válido no previsto | Comprobaciones sobre la regla, no sobre el camino (research R3); si una corrida falla por un camino válido, se amplía la comprobación, no se debilita la regla |
| Variación entre corridas | Mensajes con todo lo necesario en un turno; los fallos se analizan en el registro antes de tocar la aserción |
| La clave no está en el entorno de Claude Code | El desarrollador corre la suite y se anota el resultado en `tasks.md`, como en el #12 |
| Costo y duración de la suite | Un turno por caso; SC-005 vigila la duración |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
