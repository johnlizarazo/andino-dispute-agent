# Feature Specification: Escalamiento con criterio y solicitudes múltiples

**Feature Branch**: `010-escalamiento-criterio-solicitudes`

**Created**: 2026-10-24

**Issue**: #10 (https://github.com/johnlizarazo/andino-dispute-agent/issues/10)

**Status**: Approved

**Input**: Issue #10: escalar de inmediato cuando el cliente pide una persona (regla 4),
escalar cuando la política no cubre el caso o la disputa supera el umbral (reglas 2 y 5),
resolver solicitudes con varios asuntos y no escalar lo que el agente puede resolver. Casos de
prueba: el mensaje de ejemplo, un cliente que pide una persona desde el primer mensaje y un
cobro que la política no cubre.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Cliente ficticio**: escribe uno o varios asuntos en un mensaje; puede pedir una persona.
- **Agente de disputas**: decide qué hacer con cada asunto y cuándo escalar.
- **Controles del agente** (hooks): registran los escalamientos pendientes y no dejan cerrar
  el turno sin escalarlos.
- **Analista humano**: recibe el caso con un resumen completo (handoff).

### User Story 1 - Un escalamiento obligatorio no se puede omitir (Priority: P1)

Como banco, quiero que, si una disputa se niega por superar el umbral o la política no cubre
el cobro, el agente no pueda terminar su respuesta sin escalar el caso a un analista, para que
el cliente nunca quede sin respuesta aunque el modelo lo olvide.

**Why this priority**: es la garantía determinista que la constitución exige (principio II)
para las reglas 2 y 5.

**Independent Test**: registrar una disputa negada por umbral sin escalamiento posterior y
comprobar que los controles impiden terminar el turno con una razón que pide escalar; tras un
escalamiento exitoso de esa transacción, el turno puede terminar.

**Acceptance Scenarios**:

1. **Given** una disputa negada por superar el umbral en la conversación, **When** el agente
   intenta terminar su respuesta sin haber escalado esa transacción, **Then** los controles lo
   impiden y le devuelven una razón que indica escalar con causa umbral.
2. **Given** una disputa que el core rechaza por estar fuera de política, **When** el agente
   intenta terminar sin escalarla, **Then** se le impide con una razón que indica escalar con
   causa fuera de política.
3. **Given** un escalamiento pendiente, **When** el agente escala con éxito incluyendo esa
   transacción, **Then** el pendiente se limpia y el turno puede terminar.
4. **Given** un escalamiento pendiente, **When** el agente escala sin incluir esa transacción
   o el escalamiento falla, **Then** el pendiente sigue y el turno no puede terminar todavía.
5. **Given** que el escalamiento sigue fallando (por ejemplo, una falla transitoria), **When**
   los controles ya impidieron terminar el turno el número máximo de veces, **Then** dejan
   terminar y el cliente recibe un aviso claro de que el caso no pudo pasar a un analista.

---

### User Story 2 - El pendiente no bloquea lo que se puede resolver (Priority: P2)

Como cliente, quiero que, en el mismo mensaje, el agente dispute el cobro que puede disputar y
bloquee mi tarjeta aunque otro cobro deba ir a un analista, para no esperar por lo que se
resuelve de inmediato.

**Why this priority**: el mensaje de ejemplo mezcla las tres cosas; un control mal diseñado
podría bloquear lo resoluble.

**Independent Test**: con el mensaje de ejemplo (dos cobros de ayer en la tarjeta 4821, uno
de $180.000 y otro de $1.250.000, y pedido de bloqueo), con el cobro mayor ya pendiente de
escalar, comprobar que los controles autorizan disputar el cobro menor y bloquear la tarjeta.

**Acceptance Scenarios**:

1. **Given** un escalamiento pendiente por el cobro de $1.250.000, **When** el agente disputa
   el cobro de $180.000 del mismo cliente verificado, **Then** se autoriza.
2. **Given** el mismo pendiente, **When** el agente bloquea la tarjeta del cliente verificado,
   **Then** se autoriza.
3. **Given** dos transacciones pendientes de escalar, **When** el agente escala una sola,
   **Then** el turno sigue sin poder terminar hasta escalar la otra (o ambas en un mismo
   escalamiento).

---

### User Story 3 - Persona a pedido y escalamiento con criterio (Priority: P3)

Como cliente, quiero que, si pido hablar con una persona, el agente me escale de inmediato sin
hacerme preguntas; y como banco, quiero que el agente no escale lo que puede resolver solo,
para no saturar a los analistas.

**Why this priority**: es la regla 4 y el equilibrio del escalamiento; exige interpretar al
cliente, así que se orienta con instrucciones y ejemplos (no con un control determinista).

**Independent Test**: conversación manual con un cliente que pide una persona desde el primer
mensaje; otra con una frase que menciona a una persona pero no pide hablar con una
("una persona me clonó la tarjeta"); otra con una disputa bajo el umbral.

**Acceptance Scenarios**:

1. **Given** un primer mensaje que pide hablar con una persona, **When** el agente responde,
   **Then** escala de inmediato con causa persona solicitada, sin buscar, verificar ni
   consultar nada antes, y le informa al cliente el número de escalamiento.
2. **Given** un mensaje que menciona a una persona sin pedir hablar con una (por ejemplo, que
   alguien usó su tarjeta), **When** el agente responde, **Then** no escala por ese motivo y
   atiende el caso.
3. **Given** una disputa bajo el umbral o un pedido de bloqueo, **When** el agente lo resuelve,
   **Then** no escala.
4. **Given** un cliente molesto que no pide una persona, **When** el agente responde, **Then**
   no escala solo por la molestia.
5. **Given** la descripción de la herramienta de escalamiento, **When** se lee, **Then** dice
   cuándo usarla (de inmediato si el cliente pide una persona) y cuándo no (solo porque el
   cliente esté molesto).

---

### User Story 4 - Varios asuntos, una respuesta (Priority: P4)

Como cliente, quiero escribir todo lo que me pasa en un mensaje y recibir una sola respuesta
que diga qué pasó con cada cosa, para no repetirme.

**Why this priority**: el mensaje de ejemplo trae tres asuntos (dos cobros y un bloqueo).

**Independent Test**: conversación manual con el mensaje de ejemplo: la respuesta final
menciona la disputa del cobro menor (con número de caso), el escalamiento del cobro mayor
(con número de escalamiento) y el bloqueo de la tarjeta.

**Acceptance Scenarios**:

1. **Given** un mensaje con varios asuntos, **When** el agente lo atiende, **Then** separa los
   asuntos, resuelve cada uno y responde una sola vez con el resultado de todos.
2. **Given** que uno de los asuntos falla o se escala, **When** el agente responde, **Then** la
   respuesta unificada lo dice sin ocultar los demás resultados.

---

### User Story 5 - Ejemplos en el prompt sin contaminar los tests (Priority: P5)

Como evaluador, quiero que el prompt de sistema traiga entre 3 y 5 ejemplos que muestren la
acción esperada, y que esos ejemplos no coincidan con los mensajes de los tests de escenario,
para que un test no pase por memoria.

**Why this priority**: es el mecanismo de la regla 4 (principio II) y una exigencia del
principio VI.

**Independent Test**: revisar el prompt: entre 3 y 5 ejemplos dentro de `<ejemplos>`, cada uno
con mensaje y acción esperada; comparar sus mensajes, montos y tarjetas con los de los tests de
escenario y los datos del mensaje de ejemplo.

**Acceptance Scenarios**:

1. **Given** el prompt, **When** se revisa, **Then** tiene entre 3 y 5 ejemplos que cubren:
   pedido de persona (positivo), mención de una persona que no es un pedido (negativo),
   separación de varios asuntos y escalamiento ante un caso fuera de política.
2. **Given** cada ejemplo, **When** se lee, **Then** muestra la acción esperada (qué
   herramientas, en qué orden, qué se responde), no solo la clasificación.
3. **Given** los ejemplos y los tests de escenario, **When** se comparan, **Then** no comparten
   mensajes, montos ni últimos 4 de tarjeta.

---

### User Story 6 - Ajustes heredados del #9 (Priority: P6)

Como desarrollador, quiero cerrar las tareas pendientes y los no bloqueantes de las revisiones
del #9, para no arrastrarlos.

**Why this priority**: dos de ellos afectan a este ticket (la lista de negaciones y la razón
del umbral).

**Independent Test**: correr la suite determinista y revisar el código y las tareas del #9.

**Acceptance Scenarios**:

1. **Given** una negación sin nombre de herramienta legible, **When** se registra, **Then**
   figura con un nombre explícito ("desconocida"), no con un valor vacío.
2. **Given** la razón de negación por umbral, **When** se lee, **Then** el monto que menciona
   sale de la política del banco, no de un texto fijo.
3. **Given** el código y las tareas del #9, **When** se revisan, **Then** T024 y T025 quedan
   marcadas, sin código redundante ni líneas desproporcionadamente largas.

---

### Edge Cases

- **Escalamiento sin cliente** (causa persona solicitada): no lleva transacciones; no limpia
  pendientes de transacciones, que necesitan un escalamiento con cliente.
- **La misma transacción negada dos veces**: un solo pendiente.
- **Escalamiento que incluye varias transacciones pendientes**: las limpia todas.
- **Pendiente que nace y se escala dentro del mismo turno**: el turno termina normalmente.
- **Tope alcanzado**: el turno termina, el aviso al cliente es visible y el caso no se marca
  como escalado.
- **Cliente que reconoce el cobro**: en su siguiente mensaje el pendiente ya no obliga; si
  vuelve a pedir la disputa, la nueva negación crea otro pendiente.
- **Disputa negada por identidad o titularidad**: no crea pendiente de escalamiento (no es
  umbral ni política).
- **Falla de los controles al leer una respuesta**: no inventa pendientes ni los limpia; un
  escalamiento cuya respuesta no se puede leer no cuenta como exitoso.

## Requirements *(mandatory)*

### Functional Requirements

**Escalamiento pendiente (garantía determinista)**

- **FR-001**: Los controles MUST registrar un escalamiento pendiente, con la transacción y la
  causa (umbral o fuera de política), cuando: (a) niegan una disputa por superar el umbral, o
  (b) el core responde a una disputa con rechazo por umbral o por política.
- **FR-002**: Mientras haya pendientes, los controles MUST impedir que el agente termine el
  turno y MUST devolverle una razón que indique qué transacciones escalar y con qué causa.
- **FR-003**: Un escalamiento exitoso MUST limpiar los pendientes de las transacciones que
  incluye; un escalamiento fallido, ilegible o que no incluye la transacción MUST NOT
  limpiarlos.
- **FR-004**: Los controles MUST impedir terminar el turno como máximo 2 veces por turno; al
  alcanzar el tope MUST dejar terminar, y el cliente MUST recibir un aviso claro de que su caso
  no pudo pasar a un analista.
- **FR-005**: Al empezar un nuevo mensaje del cliente, los pendientes del turno anterior MUST
  dejar de obligar (así se cubre que el cliente reconozca el cobro); si el cliente vuelve a
  pedir esa disputa, la nueva negación crea un pendiente nuevo.
- **FR-006**: Los pendientes MUST NOT impedir disputas ni bloqueos autorizados por las reglas 1
  y 2.

**Regla 4 y criterio (orientados por instrucción)**

- **FR-007**: El prompt de sistema MUST orientar a escalar de inmediato, sin investigar, cuando
  el cliente pide una persona, y a no escalar casos resolubles ni solo por molestia.
- **FR-008**: El prompt MUST incluir entre 3 y 5 ejemplos en `<ejemplos>` con la acción
  esperada, que cubran los cuatro casos de US5, con mensajes, montos y tarjetas distintos de los tests de escenario
  y del mensaje de ejemplo.
- **FR-009**: La descripción de la herramienta de escalamiento MUST decir cuándo usarla y
  cuándo no.
- **FR-010**: La petición de una persona MUST NOT detectarse con palabras clave ni con un
  control.
- **FR-011**: El prompt MUST orientar a separar varios asuntos, resolver cada uno y responder
  una sola vez con todos los resultados; el escalamiento por umbral o política MUST llevar el
  resumen completo (causa, cliente, transacciones, acciones realizadas y recomendación).

**Heredados del #9**

- **FR-012**: Los ajustes de US6.

### Key Entities

- **Escalamiento pendiente**: transacción, causa (umbral o fuera de política); vive en el
  estado de la conversación hasta que se escala con éxito o empieza el siguiente mensaje del
  cliente.
- **Intentos de cierre impedidos**: cuántas veces se impidió terminar el turno actual; vuelve
  a cero en cada mensaje del cliente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En el 100% de los turnos con una disputa negada por umbral o política, el turno
  termina con el caso escalado o, si el escalamiento falla, con el aviso visible tras como
  máximo 2 intentos impedidos.
- **SC-002**: En el mensaje de ejemplo, el cobro menor se disputa, la tarjeta se bloquea y el
  cobro mayor se escala, en una sola respuesta.
- **SC-003**: En las validaciones manuales, el cliente que pide una persona desde el primer
  mensaje queda escalado sin ninguna otra operación previa, y la frase "una persona me clonó la
  tarjeta" no produce un escalamiento por persona solicitada.
- **SC-004**: El cobro fuera de política termina escalado con causa fuera de política y el
  resumen completo.
- **SC-005**: Ninguna disputa bajo el umbral ni ningún bloqueo se escala en las validaciones
  manuales.

## Assumptions

- **Garantías por regla** (principio II):
  - Escalar tras una disputa negada por umbral o rechazada por política: **garantizada por
    control determinista** (hook `Stop` sobre los pendientes), con tope de 2 intentos para no
    forzar un ciclo sin salida.
  - Regla 4 (persona a pedido): **orientada por instrucción** (prompt con ejemplos positivos y
    negativos, descripción de la herramienta) y verificada por escenario (manual aquí; tests
    automáticos en el #13). Interpretar al cliente no se puede hacer con palabras clave.
  - No escalar lo resoluble y separar varios asuntos: **orientados por instrucción**; el control
    nunca bloquea operaciones autorizadas (FR-006).
  - Regla 5 (no disputar fuera de política): sigue **imposible por diseño** en el core (#6);
    este ticket solo agrega la obligación de escalar.
- **Qué limpia un pendiente**: un escalamiento exitoso que incluye esa transacción, o el
  siguiente mensaje del cliente (FR-005). Decisión: reconocer el cobro es interpretar al
  cliente; en lugar de detectarlo, el pendiente solo obliga dentro del turno en que nació, y el
  agente decide con el nuevo mensaje. Como el control obliga a escalar antes de terminar el
  turno, un pendiente solo sobrevive al turno si se alcanzó el tope (falla visible).
- **Tope**: 2 cierres impedidos por turno, alineado con "reintentar como máximo dos veces" del
  prompt.
- **Aviso al alcanzar el tope**: lo muestra la interfaz (hoy la línea de comandos) además de lo
  que diga el modelo, para que la falla no dependa del modelo.
- **Pendientes del core**: el control del #9 niega el umbral antes del core, pero si el core
  rechaza por umbral (segunda defensa) o por política, la respuesta del core también crea el
  pendiente.
- **Intentos de verificación agotados**: siguen orientados por el prompt (fuera de este
  ticket).
- En esta rama también se marcan T024 y T025 del #9.
