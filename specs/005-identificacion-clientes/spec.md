# Feature Specification: Identificación: `buscar_cliente` y `verificar_identidad`

**Feature Branch**: `005-identificacion-clientes`

**Created**: 2026-10-23

**Issue**: #5 (https://github.com/johnlizarazo/andino-dispute-agent/issues/5)

**Status**: Approved

**Input**: Issue #5: las dos primeras herramientas de negocio del core bancario. Buscar no
verifica identidad; con varias coincidencias se pide otro identificador; la verificación es
la base de la regla de identidad verificada. Caso de prueba: dos clientes con el mismo
nombre.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Agente de disputas**: identifica al cliente que le escribe usando las herramientas del
  core; nunca elige entre coincidencias ni da por verificado a quien solo encontró.
- **Cliente ficticio**: da su nombre, documento o los últimos 4 dígitos de su tarjeta, y un
  dato adicional para verificarse.
- **Hook del agente** (issue #9): registra al cliente como verificado solo cuando la
  verificación del core fue exitosa.

### User Story 1 - Encontrar al cliente sin confundirlo con otro (Priority: P1)

Como agente, quiero buscar al cliente por documento, nombre o últimos 4 dígitos de tarjeta y
recibir todas las coincidencias, para saber si lo identifiqué sin ambigüedad o si necesito
pedirle otro dato.

**Why this priority**: es el primer paso de cualquier conversación y el caso de prueba
obligatorio de "dos clientes con el mismo nombre".

**Independent Test**: buscar por cada criterio con los datos ficticios y verificar 0, 1 y 2
coincidencias.

**Acceptance Scenarios**:

1. **Given** un documento existente, **When** el agente busca por documento, **Then**
   recibe exactamente una coincidencia.
2. **Given** los últimos 4 dígitos de una tarjeta existente, **When** busca por ellos,
   **Then** recibe el cliente titular.
3. **Given** el nombre compartido por dos clientes, **When** busca por nombre, **Then**
   recibe las dos coincidencias, sin que el core elija ninguna.
4. **Given** un criterio que no corresponde a nadie, **When** busca, **Then** recibe una
   respuesta exitosa con una lista vacía, no un error.
5. **Given** una búsqueda por nombre, **When** se escribe con distintas mayúsculas, sin
   tildes o con solo parte del nombre, **Then** encuentra igual a los clientes cuyo nombre
   contiene todas las palabras buscadas.
6. **Given** cualquier búsqueda, **When** el core responde, **Then** las coincidencias no
   incluyen el dato de verificación ni el documento de otras personas.

---

### User Story 2 - Verificar la identidad con un dato adicional (Priority: P2)

Como agente, quiero confirmar que quien me escribe es el cliente encontrado, con un dato que
solo él conoce, para poder operar sobre sus productos.

**Why this priority**: es la base de la regla 1 de la constitución (identidad verificada),
que el issue #9 garantiza con un hook.

**Independent Test**: verificar con el dato correcto e incorrecto de un cliente de los datos.

**Acceptance Scenarios**:

1. **Given** un cliente y su dato de verificación correcto, **When** el agente verifica,
   **Then** el core confirma la identidad de ese cliente.
2. **Given** un dato incorrecto, **When** verifica, **Then** el core responde un error de
   permiso no reintentable, sin revelar el dato correcto.
3. **Given** un cliente inexistente, **When** verifica, **Then** el core responde un error de
   validación no reintentable.
4. **Given** tres verificaciones fallidas seguidas para el mismo cliente, **When** el agente
   intenta una cuarta, **Then** el core la rechaza con un error de negocio no reintentable
   aunque el dato sea correcto, y el agente debe escalar.

---

### User Story 3 - Descripciones que guían al agente (Priority: P3)

Como agente, quiero que la descripción de cada herramienta me diga cuándo usarla y cuándo
no, para no confundir buscar con verificar ni elegir entre coincidencias.

**Why this priority**: es un comportamiento obligatorio del enunciado y el principio V de la
constitución.

**Independent Test**: leer las descripciones publicadas por el servidor.

**Acceptance Scenarios**:

1. **Given** la descripción de `buscar_cliente`, **When** se lee, **Then** dice que buscar no
   verifica identidad y que, con varias coincidencias, se debe pedir otro identificador
   (documento o últimos 4 de tarjeta) sin elegir.
2. **Given** la descripción de `verificar_identidad`, **When** se lee, **Then** dice que se
   usa después de encontrar a un único cliente y que un fallo no se reintenta con otro dato
   inventado.
3. **Given** el servidor arrancado, **When** se listan sus herramientas, **Then** aparecen
   exactamente `buscar_cliente` y `verificar_identidad`.

---

### User Story 4 - Cimientos más robustos (Priority: P4)

Como desarrollador, quiero que los datos y la configuración de fallas inválidos siempre se
informen con un mensaje claro y que las herramientas accedan al repositorio y a las fallas de
una forma explícita, para que las herramientas de los issues #6 y #7 se construyan sobre una
base sólida.

**Why this priority**: son los no bloqueantes que dejó la revisión del issue #4; conviene
resolverlos antes de sumar herramientas.

**Independent Test**: cargar datos y configuraciones con tipos incorrectos y verificar el
mensaje claro.

**Acceptance Scenarios**:

1. **Given** datos con un tipo incorrecto (un monto con decimales o booleano, un documento
   que no es texto, un registro que no es un objeto), **When** se cargan, **Then** el core no
   arranca y el mensaje nombra el archivo y el registro.
2. **Given** una tarjeta con estado distinto de activa o bloqueada, o un país que no es un
   código de 2 letras, **When** se cargan los datos, **Then** se rechazan.
3. **Given** una configuración de fallas con dígitos no ASCII, varios signos o una operación
   repetida, **When** el core arranca, **Then** informa la configuración inválida en vez de
   fallar con una traza.
4. **Given** una herramienta, **When** necesita los datos o las fallas, **Then** los obtiene
   de un contexto explícito del servidor, no de atributos agregados al vuelo.

---

### Edge Cases

- **Búsqueda sin criterio o con más de uno a la vez**: error de validación que explica que
  se usa exactamente un criterio.
- **Últimos 4 con letras o con otra longitud**: error de validación.
- **Documento con formato no ficticio**: error de validación (el core nunca acepta un
  documento que parezca real).
- **Nombre vacío o de una sola letra**: error de validación, para no devolver a todos los
  clientes.
- **Últimos 4 compartidos por tarjetas de distintos clientes**: devuelve todos los
  titulares; es otro caso de varias coincidencias.
- **Falla transitoria inyectada**: ambas herramientas la respetan (error transitorio
  reintentable).
- **Verificación exitosa después de fallos**: reinicia el contador de intentos.

## Requirements *(mandatory)*

### Functional Requirements

**Búsqueda**

- **FR-001**: `buscar_cliente` MUST aceptar exactamente uno de estos criterios: documento,
  nombre o últimos 4 dígitos de tarjeta.
- **FR-002**: MUST devolver todas las coincidencias como una respuesta exitosa con lista
  (vacía si no hay ninguna), sin elegir entre varias.
- **FR-003**: Cada coincidencia MUST incluir solo el identificador del cliente y su nombre;
  nunca el dato de verificación ni el documento.
- **FR-004**: La búsqueda por nombre MUST ignorar mayúsculas y tildes y coincidir cuando el
  nombre del cliente contiene todas las palabras buscadas.
- **FR-005**: Criterios ausentes, múltiples o mal formados MUST devolver un error de
  validación no reintentable con un mensaje que explique el formato esperado.

**Verificación**

- **FR-006**: `verificar_identidad` MUST recibir el identificador del cliente y un dato de
  verificación, y confirmar la identidad solo si el dato coincide exactamente.
- **FR-007**: Un dato incorrecto MUST devolver un error de permiso no reintentable que no
  revele el dato correcto.
- **FR-008**: Un cliente inexistente MUST devolver un error de validación no reintentable.
- **FR-009**: Tras 3 verificaciones fallidas consecutivas para un cliente, las siguientes
  MUST rechazarse con un error de negocio no reintentable mientras el core siga en marcha;
  una verificación exitosa reinicia el contador.
- **FR-010**: El core MUST no guardar sesiones de identidad: quién está verificado en la
  conversación lo controla el agente (issue #9).

**Descripciones e integración**

- **FR-011**: Las descripciones MUST cumplir US3 (buscar no verifica; con varias
  coincidencias se pide otro identificador; verificar va después de una coincidencia única).
- **FR-012**: Ambas herramientas MUST respetar la inyección de fallas transitorias por su
  nombre.
- **FR-013**: Todas las respuestas MUST seguir el contrato de errores del issue #4.

**Cimientos (heredados del issue #4)**

- **FR-014**: La carga de datos MUST rechazar con `DatosInvalidosError` y un mensaje claro
  los tipos incorrectos, los estados de tarjeta distintos de activa o bloqueada y los países
  que no sean un código de 2 letras; y validar dígitos solo ASCII.
- **FR-015**: La configuración de fallas MUST rechazar con su error propio los dígitos no
  ASCII, los signos múltiples y las operaciones repetidas.
- **FR-016**: Las herramientas MUST acceder al repositorio y al inyector de fallas a través
  de un contexto explícito del servidor.

### Key Entities

- **Coincidencia de búsqueda**: identificador del cliente y nombre.
- **Resultado de verificación**: identificador del cliente y confirmación.
- **Contador de intentos fallidos**: por cliente, en memoria del core.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El caso obligatorio de dos clientes con el mismo nombre devuelve 2
  coincidencias en el 100% de las búsquedas por ese nombre.
- **SC-002**: El 100% de las búsquedas por documento o por últimos 4 de un cliente sin
  homónimos de tarjeta devuelve exactamente 1 coincidencia.
- **SC-003**: Cero respuestas de búsqueda incluyen el dato de verificación o un documento.
- **SC-004**: El 100% de las verificaciones con dato incorrecto se rechazan como permiso no
  reintentable, y el 100% con dato correcto se confirman (mientras no se supere el límite).
- **SC-005**: Ningún dato o configuración inválidos producen una traza de error: el 100%
  termina con un mensaje que nombra el problema.

## Assumptions

- **Exponer lo mínimo**: la búsqueda devuelve solo identificador y nombre. Para desambiguar,
  el agente pide al cliente otro identificador y vuelve a buscar; no necesita ver datos de
  otras personas.
- **Límite de 3 intentos**: evita que un agente o un atacante prueben datos de verificación
  hasta acertar; vive en memoria del core (se reinicia al reiniciarlo), suficiente para la
  demo.
- **Dato de verificación**: es el año ficticio de `dato_verificacion` de los datos del #4.
- **Últimos 4 compartidos**: los datos actuales no repiten últimos 4; el comportamiento se
  prueba con datos de prueba.
- En esta rama también se marcan T029 y T030 del issue #4, como se acordó.
- Fuera de alcance: el control de identidad verificada en el agente (issue #9) y las demás
  herramientas (issues #6 y #7).
