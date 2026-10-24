---

description: "Lista de tareas del issue #13: Suite de casos obligatorios y README"
---

# Tasks: Suite de casos obligatorios y README

**Input**: documentos de diseño en `specs/013-suite-casos-obligatorios/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: el issue es una suite de tests. Los ayudantes (`registro.py`, `casos.py`) tienen su
test determinista junto a ellos, escrito **antes** que el ayudante y visto fallar. Los
escenarios van en `tests/escenarios/`, marcados `e2e`, con mensajes distintos de los
ejemplos del prompt. Solo datos ficticios; los datos de verificación se leen del core en
tiempo de ejecución. No se toca `src/`.

**Organization**: fundación (`registro.py`) → US3 (`casos.py` y su test) → US1 y US2 (suite)
→ US4 (README) → verificación. US1 y US2 comparten el archivo de la suite y van juntas.
Herramienta Bash: no escribir con scripts texto que lleve barras invertidas; usar
Write/Edit. El hook `formatear` aplica ruff (B023, BLE001, …).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US4).

---

## Phase 1: Foundational - Registro de operaciones (bloquea US1/US2)

**Purpose**: data-model `Llamada` y `Registro` (research R1).

- [X] T001 Escribir `tests/escenarios/test_registro.py`, **antes** del ayudante, con mensajes del SDK construidos a mano (`AssistantMessage` con `ToolUseBlock`, `UserMessage` con `ToolResultBlock` cuyo `content` es `[{"type": "text", "text": json.dumps(contrato)}]`, `ResultMessage`) y un `EstadoSesion`: `armar_registro` devuelve las llamadas en el orden de los `ToolUseBlock`; `herramienta` es el nombre corto "sin prefijo `mcp__core-bancario__`" (y `Agent` queda como `Agent`); `argumentos` es el `input`; `respuesta` es el contrato leído o `None` "si no llegó o no se pudo leer"; `negada` es el código del control si el `tool_use_id` está en las negaciones agregadas desde `inicio_negaciones`, y `None` si no (las anteriores no cuentan); `ok` y `codigo` derivan de la respuesta; las llamadas con `parent_tool_use_id` (subagente) se excluyen; `pendientes` es una copia de `estado.pendientes`; `estado` y `texto` vienen de `procesar_turno`. Consultas: `de("iniciar_disputa")`, `primera()` (y `None` sin llamadas), `escalamientos("umbral")` solo con los exitosos de esa causa. Verlo fallar
- [X] T002 Escribir `tests/escenarios/registro.py` (docstring: registro de lo que hizo el agente en un turno, para comprobar sin mirar el texto; research R1): `Llamada` y `Registro` (`dataclass(frozen=True)`), `armar_registro(mensajes, estado, inicio_negaciones, resultado)` pura reutilizando `leer_respuesta` de `agente_disputas.controles`, y `conversar(mensaje, entorno=None) -> Registro`, que crea `Controles.desde_entorno(entorno)`, abre `ClaudeSDKClient(options=crear_opciones(entorno, controles))`, envía el mensaje, guarda cada mensaje de `receive_response()` mientras `procesar_turno` lo consume y arma el registro. Dejar verde. Commit `test(#13): registro de operaciones del turno`

---

## Phase 2: User Story 3 - Mensajes que no pasan por memoria (Priority: P2)

**Goal**: FR-006, FR-012, SC-002 (research R4, R6). Va antes de la suite porque la suite usa `casos.py`.

**Independent Test**: `uv run pytest tests/escenarios/test_mensajes.py`.

- [X] T003 [US3] Escribir `tests/escenarios/test_mensajes.py`, **antes** de `casos.py`: hay exactamente seis claves en `MENSAJES` (`mensaje_de_ejemplo`, `persona`, `homonimos`, `sin_identidad`, `falla_transitoria`, `fuera_de_politica`); tras normalizar (minúsculas, sin tildes ni signos, espacios simples), ningún mensaje contiene un ejemplo `Cliente: "..."` de `PROMPT_SISTEMA` ni es contenido por el prompt, y ningún mensaje comparte con el prompt una secuencia de 8 palabras seguidas; `mensaje(caso)` agrega el dato de verificación leído de `Repositorio().clientes` para los casos 1 y 6 y deja igual los demás; ningún mensaje lleva un dato de verificación literal. Probar también la función de ventanas de 8 palabras con un caso que la dispara. Verlo fallar
- [X] T004 [US3] Escribir `tests/escenarios/casos.py`: `MENSAJES` con las seis plantillas en palabras propias según [contracts/casos.md](contracts/casos.md) (caso 1: documento de `CLI-001`, dos cobros de ayer en la 4821 de $180.000 y $1.250.000 que no hizo, y pedido de bloquear; caso 2: sin identificarse, quiere que lo atienda alguien del banco; caso 3: se presenta con el nombre compartido por `CLI-002` y `CLI-003`, leído de los datos, y pide revisar un cobro; caso 4: sin identificarse, pide abrir una disputa por un cobro concreto; caso 5: documento de `CLI-002`, quiere revisar movimientos, sin dato de verificación; caso 6: documento de `CLI-004`, reclama una compra de una tienda del exterior de hace unos cuatro meses en la 3344), y `mensaje(caso)`. Ninguna frase igual a los mensajes de `test_eventos_e2e.py`, `test_delegacion_e2e.py` ni del prompt. Dejar verde. Commit `test(#13): mensajes de los casos obligatorios`

---

## Phase 3: User Story 1 y 2 - Un test por caso; umbral y política escalan (Priority: P1) 🎯 MVP

**Goal**: FR-001 a FR-005, FR-007 ([contracts/casos.md](contracts/casos.md), research R2, R3, R5).

**Independent Test**: `uv run pytest -m e2e tests/escenarios/test_casos_obligatorios.py` (con credencial).

- [X] T005 [US1] [US2] Escribir `tests/escenarios/test_casos_obligatorios.py` (docstring: los seis casos obligatorios, dueña única; marca `e2e` y `skipif` sin `ANTHROPIC_API_KEY`, como los demás escenarios) con `test_caso_1_mensaje_de_ejemplo` … `test_caso_6_fuera_de_politica`, cada uno con `conversar(mensaje(caso))` y exactamente las comprobaciones de su fila del contrato. En todos: `estado == "completado"`. Caso 1 y caso 6 (US2): un escalamiento exitoso con la causa (`umbral` / `fuera_de_politica`) cuyas `transacciones` incluyen `TRX-002` / `TRX-006`, y `pendientes == {}`. Caso 2: `primera()` es `escalar_a_analista`, ok, causa `persona_solicitada`. Caso 5: dos conversaciones con `CORE_BANCARIO_FALLAS` en `buscar_cliente:1` y `buscar_cliente:5`. Cada aserción con un mensaje que muestre las llamadas del registro, para diagnosticar una falla sin repetir la corrida. Ninguna aserción sobre `texto`, salvo en el caso 5: el texto no contiene ningún valor de `Codigo` de `core_bancario_mcp.errores` (ajuste I1, FR-003)
- [X] T006 [US1] En `tests/escenarios/test_conversacion_e2e.py`: quitar `test_falla_transitoria_se_reintenta_y_el_turno_se_completa`, `test_falla_persistente_se_rinde_y_ofrece_escalar` y lo que solo usaban ellos (`MENSAJE`, `_un_turno`, `BUSCAR`, `time`, `VARIABLE_FALLAS`), dejando `test_sin_prompt_de_sistema_la_disputa_sin_identidad_no_llega_al_core`; actualizar el docstring para decir que los casos obligatorios viven en `test_casos_obligatorios.py`. `uv run pytest` en verde y ruff limpio. Commit `test(#13): suite de casos obligatorios`
- [X] T007 [US1] Correr `uv run pytest -m e2e tests/escenarios/test_casos_obligatorios.py` con la credencial (si no está en el entorno de Claude Code, la corre el desarrollador) y anotar aquí el resultado y la duración (SC-001, SC-005). Si un caso falla por un camino válido no previsto, ampliar la comprobación sin debilitar la regla y anotar el motivo; si falla por un comportamiento incorrecto del agente, detenerse y consultar al desarrollador (no se corrige el agente en este ticket). Resultado (2026-10-24, corrido por el desarrollador con su clave): `6 passed in 68.47s`; los seis casos en la primera corrida y sin ajustar comprobaciones (SC-001); duración muy por debajo de 10 minutos (SC-005)

**Checkpoint**: los seis casos tienen su test y pasan.

---

## Phase 4: User Story 4 - README en 5 minutos (Priority: P2)

**Goal**: FR-008 a FR-011, SC-004 (research R7).

**Independent Test**: quickstart paso 4.

- [X] T008 [US4] Reorganizar `README.md` conservando la cabecera (Project y marcador de video) y las secciones de desarrollo (token de GitHub, convenciones, guardrails) al final: **Inicio rápido** con dos bloques, PowerShell y bash/zsh, para definir `ANTHROPIC_API_KEY` solo en la sesión (sin escribirla en archivos), `uv sync`, `uv run pytest`, `uv run python -m agente_disputas` y `uv run andino-chat`; **Escenarios** con `uv run pytest -m e2e`, cuánto tardan y que consumen la API; **Casos obligatorios**: tabla con caso, test que lo cubre y un mensaje de ejemplo para el chat (en palabras distintas de las de `casos.py` y del prompt); la sección **Interfaz de chat** existente se mantiene. Commit `docs(#13): README con inicio rápido y casos obligatorios`

---

## Phase 5: Verificación y cierre

- [X] T009 Verificación final: `uv run pytest` en verde sin credencial (los escenarios se omiten), `uv run ruff check src tests` y `uv run ruff format --check src tests` limpios, `uv run pytest -m e2e` completo en verde (corre el desarrollador si hace falta), y la prueba de 5 minutos del README (quickstart paso 4) anotada aquí. Revisar a mano, en el chat, que en el caso 3 el agente pide otro identificador y que en el caso 5 con falla persistente ofrece escalar (ajuste I1). Para Linux/macOS (ajuste C1): revisar que cada comando de bash/zsh del README equivale al de PowerShell; si no se prueba en una máquina Linux o macOS real, anotarlo aquí y declararlo en el PR como límite conocido. Luego `/abrir-pr`. Revisiones a mano (2026-10-24): caso 5 con `buscar_cliente:5` → tres "⚠️ No se pudo completar" y una respuesta sin detalles técnicos que ofrece escalar con un analista o reintentar más tarde: cumple. Hallazgo del #12: el título del evento dice "la operación" porque `buscar_cliente` no está en `OPERACIONES` de `eventos.py` (no bloqueante 3 de la revisión del #12). Caso 3 ("Buenas, soy Carlos Andrés Pérez y tengo una duda con un cobro") → el agente dijo que encontró más de un cliente con ese nombre y pidió el documento o los últimos 4 de la tarjeta, sin verificar ni operar: cumple. Cierre (2026-10-24): `uv run pytest` → 652 passed sin credencial (escenarios omitidos); `ruff check` y `ruff format --check` limpios en `src` y `tests`; suite de casos obligatorios 6/6 con la API (T007). SC-004: el desarrollador confirmó que siguiendo el README se corre el proyecto en menos de 5 minutos (Windows). Límites declarados para el PR: los comandos de bash/zsh se revisaron para que equivalgan a los de PowerShell, pero no se probaron en una máquina Linux o macOS real; `uv run pytest -m e2e` completo (delegación, eventos y regla 1 sin prompt) no se volvió a correr después de este ticket, que no cambia nada de lo que esos escenarios comprueban

---

## Phase 6: Ajuste pedido en la revisión manual

- [X] T010 En la revisión manual del caso 5 (T009), los eventos de las búsquedas fallidas decían "No se pudo completar: la operación", porque `buscar_cliente` no está en `OPERACIONES` de `src/agente_disputas/eventos.py` (no bloqueante 3 de la revisión del #12). A pedido del desarrollador: en `src/agente_disputas/test_eventos.py`, **antes** del código, agregar `BUSCAR` a la parametrización de `test_falla_del_core` y un test de que una búsqueda sin resultado al `cerrar()` da "No se pudo completar: Búsqueda del cliente"; verlo fallar. Luego agregar `BUSCAR: "Búsqueda del cliente"` a `OPERACIONES` y la constante `BUSCAR` en `controles.py`, junto a las demás herramientas. Las búsquedas exitosas siguen sin producir evento. `uv run pytest` en verde. Commit `fix(#13): nombre de negocio de la búsqueda en los eventos`

- [X] T011 [US4] A pedido del desarrollador: los datos ficticios están fijos en `src/core_bancario_mcp/datos/` y quien prueba el agente necesita conocerlos. Agregar a `README.md` una sección **Datos de prueba**, enlazada desde el inicio rápido, con: clientes (documento, nombre, dato de verificación, tarjetas y estado), cobros (id, tarjeta, antigüedad relativa a hoy, monto, comercio, país y para qué caso sirve), política (umbral de $500.000 inclusive, 90 días en el exterior, 120 nacionales) y comportamientos útiles (homónimos, tarjeta ya bloqueada, 3 fallos de verificación bloquean la verificación, cada conversación arranca con el core en su estado inicial). Verificar cada valor contra los JSON. Commit `docs(#13): datos de prueba en el README`

## Dependencies & Execution Order

- **T001 → T002** bloquea T005.
- **T003 → T004** bloquea T005 (la suite usa `mensaje(caso)`).
- T001–T002 y T003–T004 son independientes entre sí: se pueden hacer en paralelo.
- **T005 → T006 → T007**.
- **T008** depende solo de conocer los nombres de los tests (T005); puede ir en paralelo con T006–T007.
- **T009** va al final.

## Parallel Example

```text
Fases 1 y 2: T001–T002 (registro.py) en paralelo con T003–T004 (casos.py).
Fase 3/4: T008 (README) en paralelo con T006–T007.
```

## Implementation Strategy

- **MVP**: T001–T007 dejan los seis casos cubiertos y verificados.
- Cada fase termina con `uv run pytest` en verde y su commit.
- Una falla de un escenario se diagnostica con el registro antes de tocar una aserción.
