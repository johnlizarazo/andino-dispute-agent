---

description: "Lista de tareas del issue #12: Interfaz de chat"
---

# Tasks: Interfaz de chat

**Input**: documentos de diseño en `specs/012-interfaz-chat/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la constitución los exige en dos niveles (principio VI). Cada test determinista se
escribe **antes** que el código, vive junto al módulo y se ve fallar antes de implementar. El
escenario `e2e` va en `tests/escenarios/`, marcado `e2e`, con mensajes distintos de los
ejemplos del prompt. Solo datos ficticios (`CLI-00N`, `TRX-00N`, `CC-FIC-000N`, últimos 4).

**Organization**: sonda con la API → fundación (`Negacion.tool_use_id`) → US2/US3
(`eventos.py`) → US1 (`sesion.py`) → US1/US4 (`interfaz.py` y arranque) → escenario e2e →
verificación y cierre. US2 y US3 comparten el lector de eventos y van juntas. Herramienta
Bash: no escribir con scripts texto que lleve barras invertidas; usar Write/Edit. El hook
`formatear` aplica BLE001/S110: `contextlib.suppress` o `# noqa: BLE001 - <motivo>`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US4).

---

## Phase 1: Setup - Sonda del flujo de mensajes (bloquea todo)

**Purpose**: confirmar con la API lo que el plan supone (research R1, riesgos 1 y 2).
Requiere `ANTHROPIC_API_KEY` (nunca se lee ni imprime su valor).

- [X] T001 Escribir una sonda en el directorio de trabajo temporal (fuera del repositorio) que use `crear_opciones(entorno, controles)` sin cambiar el código de producción, envuelva `controles.antes_de_herramienta` para registrar el `tool_use_id` que recibe, e imprima por cada mensaje de `receive_response()` su clase, `parent_tool_use_id`, y por bloque `ToolUseBlock(id, name)` o `ToolResultBlock(tool_use_id, is_error, tipo de content)`. Conversar en dos turnos: (1) pedir bloquear la tarjeta 4821 sin identificarse (provoca una negación `SIN_IDENTIDAD` si el agente intenta la operación; si no la intenta, repetir pidiendo explícitamente que lo intente); (2) identificarse como CC-FIC-0001 verificada y pedir bloquearla. Registrar: si el hook recibe `tool_use_id` igual al `ToolUseBlock.id`; si una llamada negada produce `ToolResultBlock` (y con qué `is_error`); la forma de `content` de un resultado MCP exitoso (que `leer_respuesta` lo lea); si las llamadas del subagente llegan con `parent_tool_use_id`. Anotar el resultado en esta tarea y ajustar research R1 y el contrato de eventos si difiere. **Si el hook no recibe `tool_use_id`, detenerse y consultar al desarrollador** (las negaciones no se podrían correlacionar). Resultado (2026-10-24): `ANTHROPIC_API_KEY` no está en el entorno de Claude Code, así que la sonda se hizo sobre el código del SDK 0.2.168. (1) El hook recibe el `tool_use_id`: `Query` llama cada callback con `request_data.get("tool_use_id")` y `PreToolUseHookInput` declara `tool_use_id: str`; se usa el argumento y, si falta, el de la entrada. (2) `message_parser` convierte cada bloque `tool_result` en `ToolResultBlock(tool_use_id, content, is_error)`, y `content` llega como lista de bloques `{"type": "text", ...}`, que `leer_respuesta` ya lee. Queda pendiente para T012, con la API, saber si una llamada negada produce `ToolResultBlock`; el diseño cubre los dos casos (`cerrar()`)

---

## Phase 2: Foundational - Negaciones con `tool_use_id` (bloquea US2/US3)

**Purpose**: data-model `Negacion` (research R1). No cambia ninguna decisión de los controles.

- [X] T002 En `src/agente_disputas/test_controles.py`, **antes** del código: una negación de `antes_de_herramienta` y otra de `antes_de_delegar` llamadas con `tool_use_id="tu_1"` registran `Negacion(herramienta, codigo, "tu_1")`; con `tool_use_id=None` registran `None`; las decisiones y la salida del hook no cambian. Verlo fallar
- [X] T003 En `src/agente_disputas/controles.py`: `Negacion` gana `tool_use_id: str | None = None` ("`str | None`: el que recibe el hook `PreToolUse`; `None` si no llega"); `_responder` recibe el `tool_use_id` desde `antes_de_herramienta` y `antes_de_delegar` y lo guarda. Actualizar el docstring del módulo. Dejar verde. Commit `feat(#12): negaciones con tool_use_id`

---

## Phase 3: User Story 2 y 3 - Eventos visibles y legibles (Priority: P2) 

**Goal**: FR-004 a FR-008, FR-012, FR-013 ([contracts/eventos.md](contracts/eventos.md)).

**Independent Test**: `uv run pytest src/agente_disputas/test_eventos.py`.

- [X] T004 [US2] [US3] Escribir `src/agente_disputas/test_eventos.py`, **antes** del módulo, con mensajes del SDK construidos a mano (`AssistantMessage` con `ToolUseBlock`, `UserMessage` con `ToolResultBlock` cuyo `content` es la forma registrada en T001) y un `EstadoSesion` con negaciones: un caso por fila de la tabla del contrato (identidad éxito y falla; bloqueo con `•••• 4821` y "ya estaba bloqueada"; disputa iniciada con caso, transacción y monto en pesos del core `$180.000`; rechazo `FUERA_DE_POLITICA` y `REQUIERE_ANALISTA`; escalamiento con cada causa de `CAUSAS` en lenguaje de negocio; análisis del subagente con resultado de texto libre (no JSON) e `is_error` ausente o falso → `analisis` exito, y con `is_error` verdadero → `falla` (ajuste I1: la delegación no se lee con el contrato del core); consulta y búsqueda exitosas sin evento; falla transitoria y de validación). Además: una llamada negada produce `negacion` con la razón de negocio de su código aunque llegue un resultado (y aunque no llegue, al `cerrar()`); una respuesta ilegible o fuera del contrato → `falla`; una llamada sin resultado y sin negación → `falla` al `cerrar()`; dos llamadas en un turno → eventos en orden de resultado; cada llamada produce como máximo un evento; las negaciones de turnos anteriores no cuentan; una consulta del subagente (con `parent_tool_use_id`) negada produce `negacion`. Para todo evento: `resultado` es `exito` solo con `ok: true`, y ni `titulo` ni `detalle` contienen `mcp__`, nombres de herramientas, códigos de error crudos, `{` ni `ok`. Verlo fallar
- [X] T005 [US2] [US3] Escribir `src/agente_disputas/eventos.py` (docstring: los eventos salen de llamadas y respuestas estructuradas y del registro de negaciones, nunca del texto del modelo): `Evento` (`dataclass(frozen=True)`: `tipo` en "`identidad`, `bloqueo`, `disputa`, `rechazo_politica`, `escalamiento`, `analisis`, `negacion`, `falla`", `resultado` en "`exito`, `negado` o `falla`", `titulo`, `detalle`), las tablas de nombres de negocio (operaciones, causas, razones por código; código desconocido → "no se pudo confirmar la operación"), y `LectorEventos(estado: EstadoSesion)` que toma como base `len(estado.negaciones)` al crearse, con `leer(mensaje) -> list[Evento]` y `cerrar() -> list[Evento]`. Reutilizar `leer_respuesta`, las constantes de herramientas de `controles.py`, `HERRAMIENTA_DELEGAR` y `pesos` de `analista.py`. Dejar verde. Commit `feat(#12): lector de eventos del turno`

**Checkpoint**: los eventos de cualquier turno se pueden calcular y probar sin interfaz.

---

## Phase 4: User Story 1 - Conversar turno a turno (Priority: P1) 🎯 MVP

**Goal**: FR-001, FR-002, FR-003, FR-009, FR-011 (data-model `SesionChat`, research R3, R4).

**Independent Test**: `uv run pytest src/agente_disputas/test_sesion.py src/agente_disputas/test_cli.py`.

- [X] T006 [P] [US1] En `src/agente_disputas/cli.py` y `src/agente_disputas/test_cli.py`: `_esperar_core` pasa a `esperar_core` (pública, mismo comportamiento); actualizar sus usos y tests. Dejar verde
- [X] T007 [US1] Escribir `src/agente_disputas/test_sesion.py`, **antes** del módulo, con un cliente falso (async context manager con `query`, `receive_response` que entrega mensajes guionados, `get_mcp_status`) inyectado por una fábrica: `iniciar()` sin credencial devuelve el mensaje de `CredencialFaltanteError` sin crear el cliente; con core `failed` devuelve "El core bancario no arrancó; revisa su configuración." ; con core `connected` devuelve `None`; `turno()` entrega a `al_evento` los eventos en orden **antes** de devolver la respuesta; devuelve `resultado.texto` o `SIN_TEXTO` si completó y `AVISOS[estado]` si no; agrega `AVISO_ESCALAMIENTO_PENDIENTE` si quedan pendientes; una `ClaudeSDKError` devuelve `AVISO_SESION` y deja la sesión cerrada (los turnos siguientes devuelven `AVISO_SESION` sin llamar al cliente); dos `turno()` concurrentes se atienden en orden sin mezclarse; dos sesiones tienen `Controles` distintos (verificar en una no verifica la otra); todo `query`/`receive_response` ocurre en la misma tarea (el trabajador); `cerrar()` sale del contexto del cliente y es idempotente. Verlo fallar
- [X] T008 [US1] Escribir `src/agente_disputas/sesion.py` (docstring: una sesión por conversación; el cliente del agente solo se usa desde su trabajador, research R3): `SesionChat(entorno, fabrica_cliente=ClaudeSDKClient)` con `Controles.desde_entorno`, `crear_opciones`, `validar_credencial`, `esperar_core`, `procesar_turno` y `LectorEventos` (envolviendo `receive_response()` en un generador que pasa cada mensaje al lector y lo reenvía), una `asyncio.Queue` y un trabajador; métodos `iniciar`, `turno(texto, al_evento)` y `cerrar`. Reutilizar los avisos de `cli.py`. Sin Chainlit. Dejar verde. Commit `feat(#12): sesión de chat por conversación`

**Checkpoint**: una conversación completa funciona contra un cliente falso.

---

## Phase 5: User Story 4 - Interfaz y arranque con un comando (Priority: P3)

**Goal**: FR-010, FR-011, US1 en el navegador ([contracts/interfaz.md](contracts/interfaz.md), research R5, R6).

**Independent Test**: quickstart paso 3 (manual).

- [X] T009 [US4] Escribir `src/agente_disputas/interfaz.py` (única pieza que importa Chainlit): `on_chat_start` crea la `SesionChat` en `cl.user_session`, llama `iniciar()` y envía el aviso o `BIENVENIDA_WEB` (ajuste U1: constante propia de `interfaz.py`, sin `/salir`, con el texto "Agente de disputas de Banco Andino (ficticio). Escribe tu mensaje para empezar; los eventos importantes de la conversación aparecen como mensajes de «Evento»."); `on_message` llama `turno()` con un `al_evento` que envía cada evento como `cl.Message(author="Evento")` con el formato "`<prefijo> <título>` en una línea y, si hay, `<detalle>` debajo" (✅ exito, ⛔ negado, ⚠️ falla) y luego la respuesta con `author="Agente"`; sin sesión lista, responde el aviso guardado; `on_chat_end` llama `cerrar()`. La función de formato (`formatear_evento`) vive en `eventos.py` y se prueba en `test_eventos.py` (test primero)
- [X] T010 [P] [US4] Crear `chainlit.md` en la raíz: bienvenida corta en español que explica qué es el agente (banco y datos ficticios), qué significan los mensajes de autor `Evento` y sus prefijos, y que se puede pedir hablar con una persona. Agregar `.chainlit/` y `.files/` a `.gitignore`
- [X] T011 [US4] Verificar a mano el arranque: `uv run chainlit run src/agente_disputas/interfaz.py` abre la interfaz; sin `ANTHROPIC_API_KEY` muestra el aviso de credencial y no atiende; con ella, un turno responde. Commit `feat(#12): interfaz de chat con Chainlit`. Resultado (2026-10-24): con ese comando la página no cargaba, porque toda petición HTTP fallaba con `NoEventLoopError`: el CLI de Chainlit aplica `nest_asyncio` y en Python 3.14 eso impide que anyio detecte el event loop (reproducido aislado). Ajuste: el comando pasa a ser `uv run andino-chat` (`[project.scripts]` → `interfaz.main`, que neutraliza `nest_asyncio` antes de importar el CLI; test en `test_interfaz.py`; research R5 revisada). Chainlit 2 no muestra el nombre del autor, así que el título del evento va en negrita (contrato de la interfaz). En el navegador, con la credencial que Chainlit toma del `.env` del desarrollador: bienvenida; bloqueo de CC-FIC-0002 → "✅ Identidad verificada / Cliente CLI-002", "✅ Tarjeta bloqueada / •••• 1357" y la respuesta; en un chat nuevo (sesión independiente), disputa de TRX-002 por $1.250.000 → "✅ Identidad verificada", "⛔ Operación negada por un control del banco / Disputa: el monto supera el umbral…", "✅ Caso escalado a un analista / Caso ESC-0001…" y la respuesta, en ese orden. El caso sin credencial no se probó en el navegador, porque Chainlit carga el `.env`; lo cubre `test_sesion.py::test_sin_credencial_avisa_y_no_crea_el_cliente`

---

## Phase 6: Escenario e2e y cierre

**Purpose**: SC-001, SC-002 con la API; README; verificación del quickstart.

- [ ] T012 Escribir `tests/escenarios/test_eventos_e2e.py` (marcado `e2e`, mensajes distintos de los ejemplos del prompt, mismo estilo que `test_conversacion_e2e.py`): con `SesionChat` real, (a) un cliente ficticio verificado pide bloquear su tarjeta → eventos `identidad` exito y `bloqueo` exito en ese orden; (b) disputa de un cobro por encima del umbral → evento negado por umbral (`negacion` o `rechazo_politica`) seguido de `escalamiento` exito, en el mismo turno; (c) disputa de un cobro dentro del umbral → evento `disputa` exito; (d) un cliente sin identificar pide hablar con una persona → evento `escalamiento` exito (ajuste C1: cubre los cuatro eventos de SC-001); ningún evento `exito` sin `ok: true`. Correr `uv run pytest -m e2e tests/escenarios/test_eventos_e2e.py` y anotar el resultado aquí
- [ ] T013 [P] Actualizar `README.md`: sección de la interfaz con el comando único, requisitos (credencial en el entorno) y qué muestran los eventos. Commit `docs(#12): escenario e2e y README`
- [ ] T014 Verificación final: `uv run pytest` en verde, `uv run ruff check` y `uv run ruff format --check` limpios, quickstart paso 3 completo (tabla de casos) y prueba de legibilidad SC-003 anotada aquí. Luego `/abrir-pr`

---

## Dependencies & Execution Order

- **T001** bloquea todo (confirma la forma de los mensajes y del `tool_use_id`).
- **T002 → T003** (fundación) bloquea US2/US3 (T004–T005).
- **T004 → T005** bloquea US1 (T007–T008), porque la sesión usa el lector.
- **T006** es independiente de T004–T005 ([P]); debe estar antes de T008.
- **T007 → T008** bloquea US4 (T009–T011).
- **T010** es independiente ([P]) desde el inicio de la fase 5.
- **T012** necesita T008; **T013** es independiente ([P]); **T014** va al final.

## Parallel Example

```text
Fase 4: T006 (cli.py) en paralelo con T007 (test_sesion.py).
Fase 5: T010 (chainlit.md, .gitignore) en paralelo con T009 (interfaz.py).
Fase 6: T013 (README) en paralelo con T012 (e2e).
```

## Implementation Strategy

- **MVP**: T001–T008 dejan la conversación turno a turno con eventos probada sin interfaz;
  T009–T011 la llevan al navegador.
- Cada fase termina con `uv run pytest` en verde y su commit.
- Si T001 contradice el plan, se ajustan research y contrato antes de seguir.
