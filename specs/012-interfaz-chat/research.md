# Research: Interfaz de chat

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

## R1. De dónde salen los eventos

- **Decision**: los eventos se derivan del flujo de mensajes del SDK de un turno. Cada
  `ToolUseBlock` (en `AssistantMessage`) se empareja con su `ToolResultBlock` (en
  `UserMessage`) por `tool_use_id`; la respuesta se lee con `controles.leer_respuesta` (el
  contrato `ok`/`datos`/`error` del core). Las negaciones de los controles se reconocen porque
  `Negacion` pasa a guardar el `tool_use_id` que recibe el hook `PreToolUse`.
- **Rationale**: FR-005 exige que los eventos reflejen lo ocurrido, no el texto del modelo. El
  par llamada/resultado y el registro de negaciones de los controles son las dos fuentes
  deterministas que ya existen; correlacionar por `tool_use_id` evita depender del texto con
  que el SDK presenta una negación.
- **Alternatives considered**:
  - Leer las negaciones del contenido del `ToolResultBlock` (`is_error` + texto): depende del
    formato que el SDK dé a la razón; frágil.
  - Hooks `PostToolUse` nuevos que emitan eventos: duplicaría la lectura de respuestas y
    acoplaría los controles (garantías) con la presentación.
  - Pedirle al modelo que anuncie los eventos: viola FR-005 y el principio II.

## R2. Qué cuenta como evento y cómo se presenta

- **Decision**: tabla fija herramienta + resultado → tipo de evento (ver
  [contracts/eventos.md](contracts/eventos.md)). Solo producen eventos `verificar_identidad`,
  `bloquear_tarjeta`, `iniciar_disputa`, `escalar_a_analista`, la delegación al subagente y
  cualquier negación por control. `buscar_cliente` y `consultar_transacciones` exitosas no
  producen evento (son lecturas que no cambian nada). Los textos son de negocio y no muestran
  nombres de herramientas, códigos crudos ni JSON (FR-008).
- **Rationale**: lo que el observador necesita es lo que cambió o se impidió; una lectura
  exitosa no explica nada nuevo y llenaría el chat de ruido.
- **Alternatives considered**: mostrar todas las llamadas (ruido, y expone nombres
  internos); mostrar solo los cuatro eventos del issue (no explica por qué se niega o se
  escala: la spec ya amplió la lista, aprobada).

## R3. Una sesión de agente por conversación en Chainlit

- **Decision**: cada conversación (`on_chat_start`) crea sus `Controles` y un trabajador
  asíncrono propio que abre el `ClaudeSDKClient` con `async with` y atiende los mensajes de
  una cola; `on_message` encola el texto y espera el resultado del turno; `on_chat_end`
  cierra la cola y el trabajador cierra el cliente. Todo lo que no es Chainlit (la cola, el
  turno, los eventos) vive en un módulo probable sin Chainlit.
- **Rationale**: el SDK no admite usar un mismo `ClaudeSDKClient` desde tareas distintas
  (cancel scopes de anyio), y Chainlit ejecuta cada callback en su propia tarea. Un trabajador
  dueño del cliente resuelve eso, serializa los turnos (caso borde de mensajes concurrentes)
  y garantiza FR-002 (estado propio por conversación).
- **Alternatives considered**:
  - Guardar el cliente en `cl.user_session` y usarlo desde cada `on_message`: rompe con el
    cancel scope del SDK.
  - `query()` sin sesión por mensaje: pierde el contexto de los turnos anteriores (US1-2).

## R4. Avisos y arranque compartidos con la línea de comandos

- **Decision**: la interfaz reutiliza las constantes de aviso de `cli.py` (`AVISOS`,
  `AVISO_ESCALAMIENTO_PENDIENTE`, `AVISO_SESION`, `SIN_TEXTO`), `validar_credencial` y la
  espera del core (`_esperar_core` pasa a ser pública como `esperar_core`).
- **Rationale**: FR-009 exige los mismos avisos; una sola fuente evita que diverjan.
- **Alternatives considered**: mover los avisos a un módulo nuevo (más piezas sin necesidad;
  `cli.py` ya es su dueño).

## R5. Comando de arranque

- **Decision** (revisada en la implementación, T011): `uv run andino-chat`, entrada de
  `[project.scripts]` que apunta a `interfaz.main`, documentada en el README. `main`
  neutraliza `nest_asyncio.apply` y luego invoca el CLI de Chainlit (`run` sobre
  `interfaz.py`). `interfaz.py` es la única pieza que importa Chainlit. Se versiona un
  `chainlit.md` corto (pantalla de bienvenida) que explica qué son los eventos; `.chainlit/`
  y `.files/` (generados por Chainlit) se agregan a `.gitignore`.
- **Rationale**: el CLI de Chainlit 2.12 aplica `nest_asyncio` al importarse, y en Python
  3.14 eso impide que anyio y sniffio detecten el event loop. Con
  `uv run chainlit run src/agente_disputas/interfaz.py` toda petición HTTP fallaba con
  `NoEventLoopError` y la interfaz no cargaba (reproducido en la verificación). La interfaz
  es asíncrona de punta a punta y no necesita reentrada. La bienvenida ayuda a que un
  observador sin contexto entienda el chat (SC-003).
- **Alternatives considered**: el comando estándar de Chainlit (no funciona en Python 3.14
  por lo anterior); bajar la versión de Python (la constitución fija 3.14); un servidor
  uvicorn propio (reimplementaría el arranque de Chainlit); versionar `.chainlit/config.toml`
  (archivo generado y largo; los valores por omisión bastan).

## R6. Presentación de eventos en Chainlit

- **Decision**: cada evento es un mensaje propio con autor `Evento` y un prefijo según su
  resultado (✅ éxito, ⛔ negado, ⚠️ falla), enviado en el orden en que ocurre, antes de la
  respuesta del agente del mismo turno.
- **Rationale**: un mensaje con autor propio se ve siempre, a diferencia de los `Step`, que
  Chainlit puede colapsar u ocultar según su configuración. Fuera de alcance: diseño visual;
  basta con distinguir eventos de mensajes.
- **Alternatives considered**: `cl.Step` por herramienta (puede quedar oculto); elementos
  laterales (no quedan en el hilo de la conversación).

## R7. Verificación

- **Decision**: tests deterministas para el lector de eventos (mensajes del SDK construidos a
  mano, incluidas negaciones, fallas, respuestas ilegibles y llamadas sin resultado) y para la
  sesión (cliente falso); `Negacion.tool_use_id` en `test_controles.py`. Un escenario `e2e`
  pasa una conversación real por el lector y comprueba los eventos de bloqueo y de negación
  por umbral con escalamiento. La interfaz se verifica a mano con el quickstart.
- **Rationale**: principio VI; la parte de Chainlit es una capa delgada sin lógica propia.
- **Alternatives considered**: probar la interfaz con un navegador automatizado (costoso y
  sin valor sobre una capa sin lógica).
