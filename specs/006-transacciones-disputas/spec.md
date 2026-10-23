# Feature Specification: Transacciones y disputas: `consultar_transacciones` e `iniciar_disputa`

**Feature Branch**: `006-transacciones-disputas`

**Created**: 2026-10-23

**Issue**: #6 (https://github.com/johnlizarazo/andino-dispute-agent/issues/6)

**Status**: Approved

**Input**: Issue #6: consultar los cobros de una tarjeta en un rango de fechas e iniciar una
disputa sobre uno de ellos. Es la base de la regla del umbral de $500.000 y de la regla de
escalar cuando la política no cubre el caso. Casos de prueba: el mensaje de ejemplo y un cobro
que la política no cubre.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Agente de disputas**: consulta los cobros que el cliente reconoce o no, y abre la disputa
  de los que no reconoce.
- **Cliente ficticio**: ya verificado; dice qué tarjeta (últimos 4) y qué cobros no reconoce.
- **Hooks del agente** (issue #9): exigen identidad verificada del titular y niegan antes de
  llegar al core las disputas sobre el umbral. El core repite la regla del umbral como
  segunda defensa.

### User Story 1 - Ver los cobros de una tarjeta en un rango de fechas (Priority: P1)

Como agente, quiero listar los cobros de una tarjeta del cliente en un rango de fechas, para
identificar con él el cobro que no reconoce.

**Why this priority**: sin ver los cobros no hay disputa; es el primer paso del mensaje de
ejemplo ("no reconozco dos cobros de ayer en la tarjeta terminada en 4821").

**Independent Test**: consultar la tarjeta 4821 de su titular con el rango de ayer y obtener
exactamente los dos cobros del mensaje de ejemplo.

**Acceptance Scenarios**:

1. **Given** la tarjeta 4821 de CLI-001 y el rango "ayer a ayer", **When** el agente
   consulta, **Then** recibe los dos cobros de ayer ($180.000 y $1.250.000) con su
   identificador, fecha, monto, comercio y país.
2. **Given** un rango sin cobros, **When** consulta, **Then** recibe una respuesta exitosa con
   lista vacía, no un error.
3. **Given** una fecha con formato inválido, una fecha inicial posterior a la final o una
   fecha final en el futuro, **When** consulta, **Then** recibe un error de validación no
   reintentable que explica el formato esperado.
4. **Given** unos últimos 4 que no corresponden a una tarjeta de ese cliente, **When**
   consulta, **Then** recibe un error de validación, sin revelar si la tarjeta pertenece a
   otra persona.
5. **Given** un cobro con disputa abierta, **When** consulta, **Then** el cobro muestra el
   identificador de su caso.

---

### User Story 2 - Abrir una disputa dentro de la política y del umbral (Priority: P2)

Como agente, quiero abrir la disputa de un cobro que el cliente no reconoce y recibir un
número de caso, para darle al cliente una referencia concreta.

**Why this priority**: es el resultado que espera el cliente en el caso feliz.

**Independent Test**: disputar el cobro de $180.000 y recibir un número de caso.

**Acceptance Scenarios**:

1. **Given** el cobro de $180.000 de ayer, **When** el agente inicia la disputa con un
   motivo, **Then** el core abre un caso y devuelve su identificador, la transacción y el
   monto tomado de los datos del core.
2. **Given** el cobro de exactamente $500.000, **When** inicia la disputa, **Then** el core la
   abre (el umbral es inclusivo).
3. **Given** un cobro con disputa ya abierta, **When** intenta disputarlo de nuevo, **Then**
   recibe un error de negocio no reintentable con el número del caso existente.
4. **Given** un cobro de una tarjeta bloqueada, **When** inicia la disputa, **Then** el core
   la abre: el bloqueo no impide disputar.

---

### User Story 3 - Rechazar lo que la política o el umbral no permiten (Priority: P3)

Como banco, quiero que el core rechace con errores de negocio inequívocos las disputas que la
política no cubre o que superan el umbral, para que el agente escale en lugar de improvisar.

**Why this priority**: son las bases de las reglas 2 y 5 de la constitución y de dos casos
obligatorios (umbral y cobro fuera de política).

**Independent Test**: disputar el cobro en el exterior de 120 días y el de $1.250.000, y
recibir los dos errores de negocio con códigos distintos.

**Acceptance Scenarios**:

1. **Given** un cobro en el exterior con más de 90 días, **When** el agente inicia la
   disputa, **Then** recibe un error de negocio no reintentable con un código propio de
   "fuera de política", y el mensaje indica escalar a un analista.
2. **Given** un cobro nacional con más de 120 días, **When** inicia la disputa, **Then**
   recibe el mismo error de "fuera de política".
3. **Given** un cobro de exactamente 90 días en el exterior (o 120 nacional), **When** inicia
   la disputa, **Then** el core la abre (el límite es inclusivo).
4. **Given** el cobro de $1.250.000, **When** inicia la disputa, **Then** recibe un error de
   negocio no reintentable con un código propio de "requiere analista", y no se abre caso.
5. **Given** cualquier disputa rechazada, **When** se consultan los cobros, **Then** el cobro
   no muestra caso abierto.

---

### User Story 4 - Descripciones y robustez (Priority: P4)

Como agente, quiero que las descripciones me digan cuándo usar cada herramienta y que toda
respuesta siga el contrato, para decidir sin interpretar texto.

**Why this priority**: principio V de la constitución; las herramientas del #5 ya lo cumplen.

**Independent Test**: leer las descripciones publicadas y llamar con argumentos inválidos de
cualquier tipo.

**Acceptance Scenarios**:

1. **Given** la descripción de `consultar_transacciones`, **When** se lee, **Then** dice que
   requiere identidad verificada del titular y que se usa para ubicar el cobro antes de
   disputarlo.
2. **Given** la descripción de `iniciar_disputa`, **When** se lee, **Then** dice que el monto
   lo toma el core de sus datos y que un rechazo por política o por umbral se escala, no se
   reintenta.
3. **Given** el servidor arrancado, **When** se listan sus herramientas, **Then** aparecen las
   dos del #5 y estas dos.
4. **Given** una falla transitoria inyectada en cualquiera de las dos, **When** se llama,
   **Then** responde un error transitorio reintentable y no abre casos.

---

### User Story 5 - Ajustes heredados de la revisión del #5 (Priority: P5)

Como desarrollador, quiero cerrar los no bloqueantes que dejó la revisión del #5, para no
arrastrarlos a los siguientes tickets.

**Why this priority**: son menores y no bloquean, pero quedaron comprometidos.

**Independent Test**: correr la suite determinista y revisar los artefactos del #5.

**Acceptance Scenarios**:

1. **Given** el test de registro que no es objeto, **When** cambian los datos ficticios,
   **Then** el test sigue pasando porque calcula la posición esperada.
2. **Given** `verificar_identidad` con espacios en los extremos de sus parámetros, **When** se
   llama, **Then** los recorta como hace `buscar_cliente`; la comparación del dato sigue
   siendo exacta tras recortar.
3. **Given** `verificar_identidad` con un dato numérico enviado por el protocolo, **When** se
   llama, **Then** responde un error de validación con el contrato.
4. **Given** la spec del #5, **When** se lee, **Then** su estado refleja que fue aprobada.

---

### Edge Cases

- **Rango de un solo día**: válido (fecha inicial igual a la final).
- **Rango sin fechas**: por omisión, los últimos 30 días contando hoy (hoy y los 29
  anteriores).
- **Rango demasiado largo** (más de 365 días): error de validación, para no listar todo el
  historial.
- **Transacción inexistente**: error de validación no reintentable.
- **Cobro fuera de política y sobre el umbral a la vez**: se responde "fuera de política",
  porque la política es la que decide primero si el caso es disputable.
- **Motivo vacío o demasiado largo** (más de 500 caracteres): error de validación.
- **Argumentos de tipo incorrecto** (número, lista): error de validación con el contrato.
- **Reinicio del core**: las disputas abiertas viven en memoria y se pierden, igual que los
  intentos de verificación (suficiente para la demo).

## Requirements *(mandatory)*

### Functional Requirements

**Consulta**

- **FR-001**: `consultar_transacciones` MUST identificar la tarjeta por el identificador del
  cliente y los últimos 4 dígitos, y solo listar tarjetas de ese cliente.
- **FR-002**: MUST aceptar un rango de fechas (formato año-mes-día) opcional; sin rango,
  usa los últimos 30 días contando hoy (hoy y los 29 anteriores).
- **FR-003**: Fechas mal formadas, fecha inicial posterior a la final, fecha final futura o
  rangos de más de 365 días MUST devolver un error de validación no reintentable.
- **FR-004**: MUST devolver una lista (vacía si no hay cobros) con identificador, fecha,
  monto, comercio, país y, si existe, el caso de disputa abierto; ordenada de la más reciente
  a la más antigua.
- **FR-005**: Una tarjeta que no existe o no es del cliente MUST devolver el mismo error de
  validación, sin distinguir ambos casos.

**Disputa**

- **FR-006**: `iniciar_disputa` MUST recibir el identificador de la transacción y un motivo;
  no recibe monto: el monto SIEMPRE sale de los datos del core.
- **FR-007**: Si la transacción no existe, MUST devolver un error de validación no
  reintentable.
- **FR-008**: Si la transacción ya tiene disputa abierta, MUST devolver un error de negocio no
  reintentable con el caso existente.
- **FR-009**: Si la antigüedad del cobro supera la política (más de 90 días en el exterior,
  más de 120 nacional; límites inclusivos), MUST devolver un error de negocio no
  reintentable con un código propio de "fuera de política" que indique escalar.
- **FR-010**: Si el monto supera $500.000 (inclusivo: $500.000 se abre), MUST devolver un
  error de negocio no reintentable con un código propio de "requiere analista".
- **FR-011**: La política se evalúa antes que el umbral; un rechazo nunca abre caso.
- **FR-012**: Si pasa todas las validaciones, MUST abrir un caso con un identificador único y
  devolverlo junto con la transacción, el monto y el estado del caso.
- **FR-013**: El cobro de una tarjeta bloqueada MUST poder disputarse.

**Descripciones e integración**

- **FR-014**: Las descripciones MUST cumplir US4 (identidad verificada del titular, monto del
  core, rechazos que se escalan).
- **FR-015**: Ambas herramientas MUST respetar la inyección de fallas por su nombre, y toda
  respuesta MUST seguir el contrato de errores (incluso con argumentos de tipo incorrecto).

**Heredados del #5**

- **FR-016**: Los cuatro ajustes de US5.

### Key Entities

- **Cobro consultado**: identificador, fecha, monto, comercio, país, caso de disputa (si
  existe). Sin datos del cliente ni de la tarjeta completa.
- **Caso de disputa**: identificador único, transacción, monto (del core), motivo, estado
  ("abierta"). Uno como máximo por transacción.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Consultar la tarjeta 4821 con el rango de ayer devuelve exactamente los 2 cobros
  del mensaje de ejemplo en el 100% de las ejecuciones, para cualquier "hoy".
- **SC-002**: El 100% de las disputas sobre cobros de más de $500.000 se rechazan sin abrir
  caso, y el 100% de las de hasta $500.000 dentro de la política se abren.
- **SC-003**: El 100% de las disputas sobre cobros fuera de política se rechazan con el código
  de "fuera de política", distinto del de "requiere analista".
- **SC-004**: Ninguna respuesta queda fuera del contrato de errores, con cualquier
  combinación de argumentos.
- **SC-005**: Una transacción nunca tiene más de un caso abierto.

## Assumptions

- **Varias tarjetas con los mismos últimos 4 del mismo cliente**: se listan los cobros de
  todas (hoy no ocurre en los datos ficticios).
- **Una disputa abierta por transacción** (FR-008): regla nueva garantizada por el servidor,
  imposible por diseño (el core no abre un segundo caso); no depende de instrucciones.
- **Producto = tarjeta**: es el único producto de los datos ficticios. Se identifica por
  cliente y últimos 4 porque es lo que el agente conoce de la conversación; los últimos 4
  solos pueden repetirse entre clientes.
- **Identidad**: el core no comprueba identidad verificada (FR-010 del #5); lo hace el hook del
  #9, que puede comparar el cliente del argumento o el titular de la transacción con el
  cliente verificado.
- **Fechas**: la antigüedad y el rango se calculan respecto del "hoy" inyectable del #4.
- **Nacional vs. exterior**: país `CO` es nacional; cualquier otro, exterior.
- **Identificador de caso**: secuencial y legible (p. ej. `CASO-0001`), único mientras el core
  siga en marcha.
- **Escalar**: la decisión y la herramienta `escalar_a_analista` quedan para los issues #7 y
  #10; aquí solo se devuelve el error que lo indica.
- En esta rama también se marcan T021 y T022 del #5.
