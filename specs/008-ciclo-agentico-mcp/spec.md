# Feature Specification: Ciclo agéntico y conexión al MCP

**Feature Branch**: `008-ciclo-agentico-mcp`

**Created**: 2026-10-23

**Issue**: #8 (https://github.com/johnlizarazo/andino-dispute-agent/issues/8)

**Status**: Approved

**Input**: Issue #8: esqueleto ejecutable del agente de disputas, conectado al core bancario,
con un ciclo agéntico que continúa o termina según la razón de parada del modelo, una línea de
comandos para conversar turno a turno, un prompt de sistema versionado y manejo de los errores
reintentables del contrato del issue #4.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Cliente ficticio** (en la demo, el desarrollador o el evaluador): conversa con el agente
  desde la terminal.
- **Agente de disputas**: atiende al cliente usando solo las seis herramientas del core
  bancario.
- **Core bancario** (`core-bancario`): el servidor de los issues #4 a #7, que el agente
  arranca y usa.

### User Story 1 - Conversar con el agente turno a turno (Priority: P1)

Como cliente, quiero escribirle al agente y recibir su respuesta en la terminal, turno a turno,
manteniendo el hilo de la conversación, para resolver mi caso como en un chat.

**Why this priority**: es el esqueleto que todos los issues siguientes (#9 a #13) necesitan
para ejecutarse y probarse.

**Independent Test**: iniciar la conversación, escribir dos mensajes seguidos y comprobar que
la segunda respuesta tiene en cuenta la primera.

**Acceptance Scenarios**:

1. **Given** la conversación iniciada, **When** el cliente escribe un mensaje, **Then** el
   agente responde en español y la terminal queda esperando el siguiente mensaje.
2. **Given** una conversación con varios turnos, **When** el cliente hace referencia a algo que
   dijo antes, **Then** el agente lo recuerda (una sola conversación por sesión).
3. **Given** la terminal, **When** el cliente escribe la orden de salida o cierra la entrada,
   **Then** la conversación termina limpiamente y el core se detiene.
4. **Given** el core no puede arrancar (p. ej., configuración de fallas inválida), **When** se
   inicia la conversación, **Then** la terminal muestra un mensaje claro y termina sin traza.

---

### User Story 2 - El ciclo sigue o termina según la razón de parada (Priority: P2)

Como banco, quiero que el agente use las herramientas que necesite dentro de un turno y lo
cierre solo cuando el modelo indica que terminó, para que nunca corte a medias ni se quede
dando vueltas por reglas improvisadas.

**Why this priority**: es el criterio central del issue ("ciclo agéntico correcto").

**Independent Test**: simular respuestas del modelo con distintas razones de parada y comprobar
qué hace el ciclo en cada una, sin llamar al modelo.

**Acceptance Scenarios**:

1. **Given** el modelo pide usar herramientas, **When** el core responde, **Then** el ciclo
   continúa dentro del mismo turno hasta que el modelo indica fin de turno.
2. **Given** el modelo indica fin de turno, **When** termina de responder, **Then** el turno se
   cierra y se muestra la respuesta final al cliente.
3. **Given** un turno que alcanza el máximo de pasos de seguridad, **When** se corta, **Then**
   el cliente recibe un aviso claro de que el agente no pudo terminar y puede pedir una
   persona; este máximo es una salvaguarda documentada, no el mecanismo normal de control.
4. **Given** cualquier turno, **When** se decide si continuar o terminar, **Then** la decisión
   no depende de contar mensajes ni de buscar palabras en el texto del modelo.

---

### User Story 3 - El agente solo puede usar el core bancario (Priority: P3)

Como banco, quiero que el agente tenga acceso únicamente a las seis herramientas del core
bancario, sin pedir permisos ni usar herramientas del entorno, para que no pueda leer
archivos, ejecutar comandos ni salirse de su función.

**Why this priority**: es una garantía de seguridad que no puede depender del prompt.

**Independent Test**: revisar la configuración del agente y comprobar que solo habilita esas
seis herramientas y ninguna otra.

**Acceptance Scenarios**:

1. **Given** la configuración del agente, **When** se revisan las herramientas habilitadas,
   **Then** son exactamente `buscar_cliente`, `verificar_identidad`,
   `consultar_transacciones`, `iniciar_disputa`, `bloquear_tarjeta` y `escalar_a_analista`
   del core bancario.
2. **Given** la configuración, **When** se revisa el acceso a herramientas del entorno (leer o
   escribir archivos, ejecutar comandos, navegar), **Then** está deshabilitado.
3. **Given** una llamada a herramienta, **When** ocurre, **Then** nunca se le pide permiso
   interactivo al cliente: lo permitido está decidido de antemano.

---

### User Story 4 - Errores reintentables según el contrato (Priority: P4)

Como cliente, quiero que una falla pasajera del core no arruine la conversación y que un error
definitivo se maneje según su tipo, para recibir una respuesta útil en vez de un mensaje
técnico.

**Why this priority**: es un criterio del issue y un caso obligatorio de la prueba (falla del
servidor MCP).

**Independent Test**: con una falla transitoria inyectada en el core, pedir algo que use esa
herramienta y comprobar que el agente reintenta y responde.

**Acceptance Scenarios**:

1. **Given** el core responde un error con `reintentable: true`, **When** el agente lo recibe,
   **Then** reintenta la misma operación, como máximo dos veces.
2. **Given** el error persiste tras los reintentos, **When** el agente se rinde, **Then**
   informa al cliente que el sistema no está disponible por ahora, sin datos técnicos, y le
   ofrece escalar con un analista.
3. **Given** un error con `reintentable: false`, **When** el agente lo recibe, **Then** no
   repite la misma llamada y actúa según el tipo: validación (corrige o pide el dato), permiso
   (pide al cliente que confirme), negocio (sigue la indicación del mensaje, p. ej. escalar).
4. **Given** una falla del propio servicio del modelo (sin respuesta, saturado), **When**
   ocurre, **Then** la terminal informa que hubo un problema temporal y la conversación sigue
   disponible para reintentar el mensaje.

---

### User Story 5 - Ajustes heredados de la revisión del #7 (Priority: P5)

Como desarrollador, quiero cerrar los no bloqueantes que dejaron las revisiones del #7, para
no arrastrarlos a los siguientes tickets.

**Why this priority**: son menores; uno de ellos evita sondear identificadores de
transacción sin identidad verificada.

**Independent Test**: correr la suite determinista y revisar los artefactos del #7.

**Acceptance Scenarios**:

1. **Given** `escalar_a_analista` con una transacción que no existe o que es de otro cliente,
   **When** se llama, **Then** ambos casos responden el mismo error, sin revelar cuál es.
2. **Given** `escalar_a_analista` con causa "persona solicitada", sin cliente y con
   transacciones existentes, **When** se llama, **Then** el escalamiento se registra (hay un
   test que lo cubre).
3. **Given** el código y el plan del #7, **When** se leen, **Then** el conjunto de causas sin
   cliente queda en una sola línea con su comentario arriba, y el plan ya no menciona cambios
   en el módulo de errores que no ocurrieron.

---

### Edge Cases

- **Mensaje vacío del cliente**: la terminal lo ignora y sigue esperando (no gasta un turno).
- **Interrupción con Ctrl+C**: termina la conversación limpiamente, sin traza.
- **Sin credencial del servicio del modelo**: la terminal informa qué variable de entorno
  falta y termina sin traza.
- **El core se cae a mitad de la conversación**: el agente recibe el error de la herramienta y
  lo trata como falla; la terminal informa si la sesión ya no puede continuar.
- **Respuesta del modelo sin texto final** (solo herramientas y luego fin): la terminal muestra
  lo que haya y no se queda colgada.
- **Varias herramientas en un mismo paso**: el ciclo las atiende todas antes de seguir.

## Requirements *(mandatory)*

### Functional Requirements

**Conversación**

- **FR-001**: El sistema MUST ofrecer una línea de comandos que reciba mensajes del cliente,
  muestre las respuestas del agente y mantenga el hilo de una sola conversación por sesión.
- **FR-002**: La línea de comandos MUST terminar limpiamente con una orden de salida, con el fin
  de la entrada o con Ctrl+C, y detener el core.
- **FR-003**: Si el core no arranca o falta la credencial del servicio del modelo, MUST mostrar
  un mensaje claro y terminar sin traza.

**Ciclo agéntico**

- **FR-004**: Dentro de un turno, el ciclo MUST continuar mientras el modelo pida herramientas y
  terminar cuando el modelo indique fin de turno.
- **FR-005**: El ciclo MUST NOT decidir con contadores de mensajes ni buscando palabras en el
  texto del modelo.
- **FR-006**: MUST existir un máximo de pasos por turno como salvaguarda documentada; al
  alcanzarlo, el cliente recibe un aviso claro y la posibilidad de pedir una persona.

**Herramientas y configuración**

- **FR-007**: El agente MUST conectarse al core bancario como servidor local, arrancado por el
  propio agente.
- **FR-008**: El agente MUST tener habilitadas exactamente las seis herramientas del core y
  ninguna herramienta del entorno, sin permisos interactivos.
- **FR-009**: El prompt de sistema MUST vivir versionado en un único módulo del agente y
  orientar: rol, idioma español, las cinco reglas de negocio, cuándo usar cada herramienta,
  no inventar datos y cómo actuar ante cada tipo de error.
- **FR-010**: El modelo que usa el agente MUST ser configurable, con un valor por omisión.
- **FR-010b**: El agente MUST autenticarse ante el servicio del modelo con la clave de API del
  desarrollador, leída solo de la variable de entorno `ANTHROPIC_API_KEY`; la clave MUST NOT
  aparecer en el código, en el repositorio, en mensajes ni en registros. Si falta, aplica
  FR-003. No se recurre a otras formas de autenticación del entorno, para que el agente se
  comporte igual en cualquier máquina.

**Errores**

- **FR-011**: Ante un error reintentable, el agente MUST reintentar como máximo dos veces y,
  si persiste, informar sin datos técnicos y ofrecer escalar.
- **FR-012**: Ante un error no reintentable, el agente MUST NOT repetir la misma llamada y MUST
  actuar según el tipo de error.
- **FR-013**: Una falla del servicio del modelo MUST informarse al cliente sin cerrar la
  conversación.

**Heredados del #7**

- **FR-014**: Los tres ajustes de US5.

### Key Entities

- **Sesión de conversación**: una por ejecución de la línea de comandos; mantiene el hilo y la
  conexión con el core mientras dura.
- **Turno**: un mensaje del cliente y todo lo que el agente hace hasta indicar fin de turno (o
  alcanzar la salvaguarda).
- **Prompt de sistema**: texto versionado que orienta al agente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los turnos terminan por fin de turno del modelo, por la salvaguarda
  documentada o por un error informado; ninguno se corta por contar mensajes o por palabras.
- **SC-002**: La configuración del agente habilita exactamente 6 herramientas y 0 herramientas
  del entorno.
- **SC-003**: Con una falla transitoria inyectada una vez, el agente completa la petición del
  cliente en el mismo turno en el 100% de las ejecuciones de escenario.
- **SC-004**: Ningún arranque o cierre de la línea de comandos termina con una traza visible
  para el cliente.
- **SC-005**: El primer mensaje del agente llega en menos de 30 segundos desde que el cliente
  escribe, en condiciones normales del servicio del modelo.

## Assumptions

- **Garantías** (principio II):
  - Solo las seis herramientas y sin permisos interactivos: **garantizado por configuración**
    (determinista) y verificado con un test.
  - Continuar o terminar según la razón de parada: **por diseño** del ciclo, verificado con
    tests sin API que simulan respuestas del modelo.
  - Reintentar errores reintentables y no repetir los definitivos: **orientado por
    instrucción** y verificado con un test de escenario con falla inyectada. No es una regla de
    negocio del banco y no reintentar no causa un daño (el cliente recibe una respuesta y puede
    escalar); las reglas 1 y 2, que sí lo son, se garantizan con hooks en el #9.
- **Salvaguarda**: el máximo de pasos por turno es generoso (del orden de decenas) y existe
  solo para que un fallo no se convierta en un ciclo sin fin.
- **Prompt de sistema inicial**: los ejemplos detallados de cuándo escalar y el reconocimiento
  del pedido de persona se refinan en el #10; aquí se deja la base.
- **Modelo**: Claude Sonnet 5.5 por omisión (equilibrio entre capacidad, latencia y costo
  para un agente conversacional con herramientas), configurable por una variable de entorno
  propia del proyecto (p. ej., para usar Claude Opus 5.5 en la demo).
- **Credencial**: el desarrollador define `ANTHROPIC_API_KEY` en su entorno, como hizo con
  `GITHUB_PAT`; `.env.example` ya la lista sin valor. El agente no carga archivos `.env`
  (principio III: los secretos solo salen de variables de entorno).
- **Herramientas habilitadas y el subagente del #11**: la lista de herramientas habilitadas se
  define en un solo lugar. El #11 le agregará únicamente la herramienta de delegación del SDK
  para el subagente `analista-transacciones`; las herramientas del entorno siguen
  deshabilitadas.
- **Tests**: los deterministas no llaman al modelo; los de escenario (`e2e`) requieren la
  credencial y sus mensajes difieren de los ejemplos del prompt.
- En esta rama también se marcan T020 y T021 del #7.
