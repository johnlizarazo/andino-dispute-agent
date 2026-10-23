# Feature Specification: Bloqueo y escalamiento: `bloquear_tarjeta` y `escalar_a_analista`

**Feature Branch**: `007-bloqueo-escalamiento`

**Created**: 2026-10-23

**Issue**: #7 (https://github.com/johnlizarazo/andino-dispute-agent/issues/7)

**Status**: Approved

**Input**: Issue #7: bloquear de inmediato una tarjeta por sospecha de fraude y escalar a un
analista con un resumen útil (cliente, transacciones, montos, lo que se hizo, causa y acción
recomendada). Con estas dos, el core tiene las seis herramientas de la constitución.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Agente de disputas**: bloquea la tarjeta cuando el cliente sospecha fraude y escala
  cuando la regla lo pide (umbral, fuera de política, intentos agotados) o el cliente pide una
  persona.
- **Cliente ficticio**: pide el bloqueo o una persona; puede no estar identificado cuando pide
  una persona.
- **Analista humano** (fuera del sistema): recibe el escalamiento y debe poder actuar sin
  volver a preguntarle nada al cliente.
- **Hooks del agente** (issues #9 y #10): exigen identidad verificada antes de bloquear y, con
  la causa del escalamiento, comprueban que no quede uno pendiente.

### User Story 1 - Bloquear la tarjeta de inmediato (Priority: P1)

Como agente, quiero bloquear la tarjeta que el cliente reporta por sospecha de fraude, sin
pasos intermedios, para cortar el riesgo en el momento.

**Why this priority**: es la regla 3 de la constitución y un caso obligatorio de la prueba.

**Independent Test**: bloquear la tarjeta 4821 de CLI-001 y comprobar su nuevo estado.

**Acceptance Scenarios**:

1. **Given** la tarjeta activa 4821 de CLI-001, **When** el agente la bloquea con un motivo,
   **Then** el core la deja bloqueada en ese momento y confirma el nuevo estado.
2. **Given** una tarjeta ya bloqueada (la 9012 de CLI-004, o una bloqueada antes en la
   sesión), **When** el agente la bloquea otra vez, **Then** recibe una respuesta exitosa que
   indica que ya estaba bloqueada, no un error.
3. **Given** unos últimos 4 que no corresponden a una tarjeta de ese cliente, **When**
   intenta bloquear, **Then** recibe un error de validación, sin revelar si la tarjeta es de
   otra persona.
4. **Given** el bloqueo, **When** se busca cualquier paso de aprobación, **Then** no existe:
   la herramienta no admite ni espera la aprobación de un analista.

---

### User Story 2 - Escalar con un resumen que el analista pueda usar (Priority: P2)

Como analista, quiero recibir cada escalamiento con el cliente, las transacciones y sus
montos, lo que el agente ya hizo, la causa y la acción recomendada, para resolver el caso sin
reconstruir la conversación.

**Why this priority**: es el handoff que piden el issue y los casos obligatorios de umbral,
fuera de política y persona a pedido.

**Independent Test**: escalar el cobro de $1.250.000 con causa umbral y comprobar el
escalamiento registrado.

**Acceptance Scenarios**:

1. **Given** un resumen completo con causa "umbral", el cliente CLI-001 y la transacción de
   $1.250.000, **When** el agente escala, **Then** el core registra para el analista el
   resumen con el nombre del cliente y el monto de cada transacción tomado de sus datos, y al
   agente le devuelve solo el identificador del escalamiento, la causa, el estado y cuántas
   transacciones incluye.
2. **Given** el cliente pide hablar con una persona antes de identificarse, **When** el agente
   escala con causa "persona solicitada" y sin cliente ni transacciones, **Then** el core lo
   acepta (regla 4: se escala de inmediato, sin investigar).
3. **Given** un resumen al que le falta la causa, las acciones realizadas o la acción
   recomendada, **When** el agente escala, **Then** recibe un error de validación que nombra
   lo que falta.
4. **Given** una causa fuera de la lista cerrada, **When** escala, **Then** recibe un error de
   validación con las causas válidas.
5. **Given** una causa que exige cliente y transacciones (umbral o fuera de política) sin
   ellos, **When** escala, **Then** recibe un error de validación.
6. **Given** una transacción inexistente o que no es del cliente indicado, **When** escala,
   **Then** recibe un error de validación y no se registra el escalamiento.
7. **Given** una transacción con disputa abierta, **When** escala, **Then** el resumen
   registrado para el analista incluye el caso de esa disputa.
8. **Given** cualquier escalamiento, **When** el core responde al agente, **Then** la respuesta
   no incluye montos, fechas, comercios ni el nombre del cliente: escalar no exige identidad
   verificada y no debe servir para consultar productos (regla 1).

---

### User Story 3 - Descripciones y robustez (Priority: P3)

Como agente, quiero que las descripciones me digan cuándo usar cada herramienta y que toda
respuesta siga el contrato, para decidir sin interpretar texto.

**Why this priority**: principio V de la constitución, como en el #5 y el #6.

**Independent Test**: leer las descripciones publicadas y llamar con argumentos inválidos de
cualquier tipo.

**Acceptance Scenarios**:

1. **Given** la descripción de `bloquear_tarjeta`, **When** se lee, **Then** dice que el
   bloqueo es inmediato, que no requiere aprobación de un analista y que requiere la identidad
   verificada del titular.
2. **Given** la descripción de `escalar_a_analista`, **When** se lee, **Then** dice que no
   requiere identidad verificada, que ante un pedido de persona se escala de inmediato, que los
   montos los completa el core y cuáles son las causas válidas.
3. **Given** el servidor arrancado, **When** se listan sus herramientas, **Then** aparecen las
   seis de la constitución.
4. **Given** una falla transitoria inyectada en cualquiera de las dos, **When** se llama,
   **Then** responde un error transitorio reintentable y no bloquea ni registra nada.
5. **Given** argumentos de un tipo incorrecto (número, lista donde va texto, texto donde va
   lista), **When** se llama, **Then** responde un error de validación con el contrato.

---

### User Story 4 - Ajustes heredados de la revisión del #6 (Priority: P4)

Como desarrollador, quiero cerrar los no bloqueantes que dejó la revisión del #6, para no
arrastrarlos a los siguientes tickets.

**Why this priority**: son menores y no bloquean, pero quedaron comprometidos.

**Independent Test**: correr la suite determinista.

**Acceptance Scenarios**:

1. **Given** `consultar_transacciones` con una fecha vacía o de solo espacios, **When** se
   llama, **Then** ambas se tratan igual: como fecha omitida.
2. **Given** el registro de disputas, **When** se abren casos, **Then** su número sale de un
   contador propio y nunca se repite, aunque en el futuro se cierren casos.
3. **Given** la regla de antigüedad, **When** el core rechaza una disputa fuera de política,
   **Then** el límite que informa sale de la misma definición que usa la política, escrita una
   sola vez.

---

### Edge Cases

- **Varias tarjetas del mismo cliente con los mismos últimos 4**: se bloquean todas (hoy no
  ocurre en los datos).
- **Motivo de bloqueo vacío o demasiado largo** (más de 500 caracteres): error de validación.
- **Escalamiento con causa "persona solicitada" y cliente conocido**: se acepta con cliente;
  el cliente es opcional, no prohibido.
- **Escalamiento con causa "intentos agotados"**: exige cliente (ya se buscó y se intentó
  verificar), pero no transacciones.
- **Transacciones repetidas en el resumen**: se cuentan una vez.
- **Cliente indicado que no existe**: error de validación.
- **Varios escalamientos del mismo cliente**: se permiten; cada uno tiene su identificador.
- **Reinicio del core**: los bloqueos y escalamientos hechos en la sesión viven en memoria y
  se pierden; las tarjetas vuelven a su estado inicial de los datos (suficiente para la demo).

## Requirements *(mandatory)*

### Functional Requirements

**Bloqueo**

- **FR-001**: `bloquear_tarjeta` MUST identificar la tarjeta por el identificador del cliente y
  los últimos 4 dígitos, con el mismo error de validación si no existe o es de otro cliente.
- **FR-002**: MUST recibir un motivo (texto no vacío, hasta 500 caracteres) y bloquear en el
  mismo llamado, sin aprobación ni paso intermedio.
- **FR-003**: MUST responder éxito con el estado resultante (`bloqueada`) y si la tarjeta ya
  estaba bloqueada antes del llamado (por los datos o por un bloqueo previo en la sesión).
- **FR-004**: El estado de una tarjeta MUST ser "bloqueada" si lo era en los datos o si se
  bloqueó mientras el core sigue en marcha; nunca se desbloquea en este alcance.

**Escalamiento**

- **FR-005**: `escalar_a_analista` MUST exigir causa, acciones realizadas y acción recomendada;
  si falta alguna, error de validación que nombra los campos faltantes.
- **FR-006**: La causa MUST pertenecer a una lista cerrada: persona solicitada, umbral, fuera
  de política, intentos agotados, otra.
- **FR-007**: El cliente MUST ser obligatorio salvo con causa "persona solicitada"; si se
  indica, MUST existir.
- **FR-008**: La lista de transacciones MUST ser obligatoria y no vacía con causa "umbral" o
  "fuera de política", y opcional con las demás; cada transacción MUST existir y, si hay
  cliente, pertenecerle.
- **FR-009**: Los montos MUST salir de los datos del core por cada transacción; el resumen no
  acepta montos del agente.
- **FR-010**: MUST registrar para el analista el resumen completo: identificador único,
  causa, cliente (identificador y nombre, o ninguno), transacciones con fecha, monto, comercio
  y caso de disputa si existe, total, acciones realizadas, acción recomendada y estado
  "pendiente de analista".
- **FR-010b**: Al agente MUST devolverle solo el identificador del escalamiento, la causa, el
  estado y la cantidad de transacciones incluidas; nunca montos, fechas, comercios ni el
  nombre del cliente (ajuste C1: escalar está exento de identidad verificada y no puede ser
  una vía de consulta).
- **FR-011**: Un resumen inválido MUST no registrar nada.

**Descripciones e integración**

- **FR-012**: Las descripciones MUST cumplir US3.
- **FR-013**: Ambas herramientas MUST respetar la inyección de fallas por su nombre, y toda
  respuesta MUST seguir el contrato de errores, incluso con argumentos de tipo incorrecto.

**Heredados del #6**

- **FR-014**: Los tres ajustes de US4.

### Key Entities

- **Bloqueo**: tarjeta, motivo; marca la tarjeta como bloqueada mientras el core sigue en
  marcha.
- **Escalamiento**: identificador único, causa, cliente (opcional), transacciones con monto y
  caso, total, acciones realizadas, acción recomendada, estado "pendiente de analista".

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los bloqueos de una tarjeta propia del cliente la dejan bloqueada en
  un solo llamado, sin ningún paso de aprobación.
- **SC-002**: Bloquear una tarjeta ya bloqueada nunca produce un error.
- **SC-003**: El 100% de los escalamientos registrados para el analista contienen los seis elementos del
  handoff (o el cliente explícitamente ausente con causa "persona solicitada"), con montos
  iguales a los del core.
- **SC-004**: El 100% de los resúmenes incompletos o inválidos se rechazan sin registrar
  nada.
- **SC-005**: Ninguna respuesta queda fuera del contrato de errores, con cualquier
  combinación de argumentos.
- **SC-006**: Ninguna respuesta de `escalar_a_analista` contiene datos de productos (montos,
  fechas, comercios) ni el nombre del cliente.

## Assumptions

- **Garantías por regla** (principio II):
  - Regla 3: la ausencia de aprobación intermedia es **imposible por diseño** (la herramienta
    no tiene ese paso); la identidad verificada antes de bloquear la garantiza el hook del #9.
  - Regla 4: "persona solicitada" sin cliente ni transacciones es **posible por diseño**, para
    no frenar el escalamiento inmediato; reconocer el pedido se orienta con instrucciones y se
    verifica con tests de escenario (#10 y #13).
  - Regla 2: los montos del resumen salen del core (**imposible por diseño** que el analista
    reciba un monto del modelo).
  - Cuándo escalar y no cerrar el turno con un escalamiento pendiente: hook `Stop` del #10,
    que usará la causa.
- **Estado de la tarjeta**: el dato inicial (`activa` o `bloqueada`) sigue en los datos; los
  bloqueos de la sesión viven en memoria del core, como intentos y disputas. El hook del #9 no
  necesita el estado de la tarjeta.
- **Visibilidad del estado**: solo la respuesta de `bloquear_tarjeta` lo muestra; las otras
  herramientas no cambian su contrato.
- **Identificador de escalamiento**: secuencial y legible (p. ej. `ESC-0001`).
- **Sin desbloqueo ni cierre de escalamientos**: fuera de alcance; los resuelve el analista
  fuera del sistema.
- En esta rama también se marcan T024 y T025 del #6.
