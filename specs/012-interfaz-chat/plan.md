# Implementation Plan: Interfaz de chat

**Branch**: `012-interfaz-chat` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/012-interfaz-chat/spec.md` (issue #12)

## Summary

- **Eventos** (`eventos.py`, nuevo): `LectorEventos` empareja cada llamada a herramienta con
  su resultado por `tool_use_id`, lee la respuesta con el contrato del core y reconoce las
  negaciones de los controles; produce `Evento`s con títulos y detalles de negocio según una
  tabla fija. Sin Chainlit y sin API: se prueba con mensajes construidos a mano.
- **Controles** (`controles.py`): `Negacion` guarda el `tool_use_id` del `PreToolUse`. No
  cambia ninguna decisión.
- **Sesión** (`sesion.py`, nuevo): una por conversación, con sus `Controles` y un trabajador
  dueño del `ClaudeSDKClient` que atiende una cola de mensajes; entrega eventos en orden y la
  respuesta o el aviso final con los mismos textos que la línea de comandos.
- **Interfaz** (`interfaz.py`, nuevo): capa delgada de Chainlit (`on_chat_start`,
  `on_message`, `on_chat_end`) que muestra mensajes y eventos. Arranca con
  `uv run andino-chat`.
- **CLI** (`cli.py`): `_esperar_core` pasa a `esperar_core` para compartirla.

Decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: `chainlit` 2.12.0 (ya en `pyproject.toml`), `claude-agent-sdk`
0.2.168 (`ClaudeSDKClient`, `AssistantMessage`, `UserMessage`, `ToolUseBlock`,
`ToolResultBlock`)

**Storage**: ninguno (estado en memoria por conversación)

**Testing**: `pytest` determinista (`test_eventos.py`, `test_sesion.py` con cliente falso,
`test_controles.py`); escenario `e2e` que pasa una conversación real por el lector

**Target Platform**: navegador local contra el servidor de Chainlit; mismo entorno que la CLI

**Project Type**: aplicación de chat web local dentro del proyecto `uv`, junto a la CLI

**Performance Goals**: interfaz lista en menos de 1 minuto desde el comando (SC-004)

**Constraints**:
- La interfaz no cambia el agente, el prompt, los controles ni el core (FR-003).
- Los eventos salen de llamadas y respuestas estructuradas, nunca del texto del modelo
  (FR-005).
- Un `ClaudeSDKClient` solo se usa desde su trabajador (research R3).
- Solo `interfaz.py` importa Chainlit.

**Scale/Scope**: 3 módulos nuevos con sus tests (`eventos.py`, `sesion.py`, `interfaz.py`
sin test propio), cambios menores en `controles.py` y `cli.py`, 1 escenario `e2e`,
`chainlit.md`, `.gitignore` y README

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | Sin cambios: la interfaz usa las mismas opciones y controles; cada conversación nace con su propio estado de controles (la identidad verificada no se comparte entre pestañas). | ✅ |
| II. Garantías deterministas | No hay regla nueva de negocio. La fidelidad de los eventos se garantiza derivándolos de llamadas/respuestas y del registro de negaciones (no del modelo) y se verifica con tests deterministas. El aviso de escalamiento pendiente lo emite la interfaz. | ✅ |
| III. Datos ficticios y cero credenciales | Eventos solo con ids ficticios, últimos 4 dígitos y montos del core; la credencial se lee del entorno; `.files/` y `.chainlit/` fuera de git. | ✅ |
| IV. Spec-first | Spec aprobada en el control 1; plan y tareas antes de `src/`. | ✅ |
| V. Contrato de herramientas | Los eventos se leen con `leer_respuesta` y el contrato `ok`/`datos`/`error`; una respuesta fuera del contrato produce falla, nunca éxito. | ✅ |
| VI. Tests en dos niveles | Deterministas junto a `eventos.py`, `sesion.py` y `controles.py`; escenario `e2e` con mensajes distintos de los ejemplos del prompt. | ✅ |
| VII. Simplicidad | La lógica vive en dos módulos probables; Chainlit queda en una capa delgada; comando estándar de Chainlit, sin scripts extra. | ✅ |

**Resultado**: todos los gates pasan. **Re-evaluación tras la fase 1**: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/012-interfaz-chat/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── eventos.md
│   └── interfaz.md
├── checklists/requirements.md
└── tasks.md                     # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
src/agente_disputas/
├── eventos.py                   # nuevo: Evento, LectorEventos, textos de negocio
├── test_eventos.py              # nuevo
├── sesion.py                    # nuevo: SesionChat (trabajador + cola + turno)
├── test_sesion.py               # nuevo
├── interfaz.py                  # nuevo: callbacks de Chainlit
├── controles.py                 # mod: Negacion.tool_use_id
├── test_controles.py            # mod
├── cli.py                       # mod: esperar_core pública
└── test_cli.py                  # mod si referencia _esperar_core
tests/escenarios/test_eventos_e2e.py   # nuevo, marcado e2e
chainlit.md                      # nuevo: bienvenida que explica los eventos
.gitignore                       # mod: .chainlit/, .files/
README.md                        # mod: comando de la interfaz
```

**Structure Decision**: `eventos.py` y `sesion.py` concentran la lógica y no importan
Chainlit, para probarla sin servidor ni API; `interfaz.py` solo traduce a mensajes de
Chainlit ([research.md R3, R6](research.md)).

## Orden de implementación

1. **`Negacion.tool_use_id`** en `controles.py` (test primero).
2. **`eventos.py`** (US2, US3): tabla de [contracts/eventos.md](contracts/eventos.md), test
   primero con una prueba por fila, más negaciones, ilegibles y llamadas sin resultado.
3. **`sesion.py`** (US1, FR-002, FR-009, FR-011): trabajador, cola, turno con eventos y
   avisos; test con cliente falso.
4. **`interfaz.py`**, `chainlit.md`, `.gitignore`, `esperar_core` (US1, US4).
5. **Escenario e2e**, README y **verificación** con el [quickstart](quickstart.md), luego
   `/abrir-pr`.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El SDK no entrega un `ToolResultBlock` para una llamada negada por el hook | `cerrar()` convierte las llamadas sin resultado en `negacion` (si están en el registro) o `falla`; el e2e lo confirma con la API |
| El hook no recibe `tool_use_id` | Campo opcional; sin él, la llamada negada cae en `falla` (nunca en éxito) y el e2e lo detecta antes del PR |
| Uso del cliente desde otra tarea de Chainlit | Trabajador único dueño del cliente (research R3), probado con cliente falso |
| Eventos del subagente (consultas) llenan el chat | Las consultas exitosas no producen evento; solo sus negaciones o fallas |
| Chainlit genera archivos en la raíz | `.chainlit/` y `.files/` en `.gitignore` |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
