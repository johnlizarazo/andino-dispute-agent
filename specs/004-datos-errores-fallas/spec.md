# Feature Specification: Datos ficticios, contrato de errores e inyección de fallas

**Feature Branch**: `004-datos-errores-fallas`

**Created**: 2026-10-23

**Issue**: #4 (https://github.com/johnlizarazo/andino-dispute-agent/issues/4)

**Status**: Draft

**Input**: Issue #4: cimientos del servidor `core-bancario`, que simula el core de Banco
Andino (ficticio). Incluye errores estructurados, datos ficticios para los casos de prueba
obligatorios, fallas transitorias reproducibles y una consulta de transacciones reutilizable
por el agente.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Agente de disputas**: consume el core por sus herramientas (issues #5 a #7) y decide si
  reintenta, pregunta o escala según el error que recibe.
- **Hooks del agente** (issue #9): consultan el monto real de una transacción por su
  identificador, sin depender de lo que diga el modelo.
- **Desarrollador o evaluador**: ejecuta los casos de prueba obligatorios y necesita que los
  datos y las fallas sean reproducibles.

### User Story 1 - Errores que el agente entiende sin interpretar texto (Priority: P1)

Como agente, quiero que toda respuesta del core tenga una forma única que me diga si fue
exitosa y, si falló, de qué tipo de error se trata y si tiene sentido reintentar, para
decidir qué hacer sin interpretar mensajes en lenguaje natural.

**Why this priority**: es el principio V de la constitución y la base de todas las
herramientas de los issues #5 a #7; sin el contrato, cada herramienta inventaría su forma.

**Independent Test**: construir un error de cada tipo y una respuesta exitosa, y verificar
su forma y la marca de reintento.

**Acceptance Scenarios**:

1. **Given** una operación exitosa, **When** el core responde, **Then** la respuesta indica
   éxito e incluye los datos.
2. **Given** una falla de cualquiera de los cuatro tipos (transitorio, validación, negocio,
   permiso), **When** el core responde, **Then** la respuesta indica fracaso con tipo,
   código, mensaje y si es reintentable.
3. **Given** un error transitorio, **When** el agente lo recibe, **Then** está marcado como
   reintentable; **Given** un error de validación, negocio o permiso, **Then** está marcado
   como no reintentable.
4. **Given** una búsqueda sin resultados, **When** el core responde, **Then** es una
   respuesta exitosa con una lista vacía, no un error.

---

### User Story 2 - Datos ficticios que reproducen los casos obligatorios (Priority: P2)

Como evaluador, quiero que el core tenga datos ficticios que soporten todos los casos de
prueba obligatorios cualquier día que se ejecuten, para que la demo y los tests no dependan
de la fecha ni de datos reales.

**Why this priority**: los casos de prueba del enunciado son la evidencia de funcionamiento;
sin estos datos no se pueden ejecutar.

**Independent Test**: cargar los datos con un "hoy" arbitrario y verificar que los cobros
"de ayer" quedan en el día anterior y que existen los clientes y cobros de cada caso.

**Acceptance Scenarios**:

1. **Given** cualquier fecha de ejecución, **When** se cargan los datos, **Then** existe un
   cliente con una tarjeta terminada en 4821 que tiene exactamente dos cobros con fecha del
   día anterior: uno de $180.000 y otro de $1.250.000.
2. **Given** los datos cargados, **When** se buscan clientes por nombre, **Then** hay dos
   clientes distintos con el mismo nombre completo y datos de identificación diferentes.
3. **Given** los datos cargados, **When** se revisan los cobros, **Then** existe un cobro de
   un comercio en el exterior con más de 90 días de antigüedad respecto de la fecha de
   ejecución.
4. **Given** los datos, **When** se inspeccionan, **Then** las tarjetas aparecen solo con sus
   últimos 4 dígitos y los documentos tienen formato ficticio (`CC-FIC-NNNN`).
5. **Given** la política del banco, **When** se consulta, **Then** declara la regla de
   cobertura para cobros en el exterior (hasta 90 días) que el caso de "cobro no cubierto"
   necesita.

---

### User Story 3 - Fallas transitorias reproducibles (Priority: P3)

Como evaluador, quiero poder hacer que una herramienta del core falle de forma transitoria
un número determinado de veces, para demostrar que el agente maneja la falla del servidor
como pide el caso de prueba obligatorio.

**Why this priority**: es un caso de prueba obligatorio; requiere que la falla sea
controlable y repetible, no aleatoria.

**Independent Test**: configurar que una operación falle N veces y verificar que las
primeras N llamadas devuelven un error transitorio reintentable y la siguiente funciona.

**Acceptance Scenarios**:

1. **Given** la configuración "operación X falla 2 veces", **When** se llama a X tres veces,
   **Then** las dos primeras devuelven un error transitorio reintentable y la tercera
   responde normalmente.
2. **Given** ninguna configuración de fallas, **When** se llama a cualquier operación,
   **Then** nunca falla por inyección.
3. **Given** una configuración mal escrita, **When** el core arranca, **Then** informa el
   problema de forma clara en vez de ignorarlo en silencio.
4. **Given** la falla configurada para la operación X, **When** se llama a otra operación Y,
   **Then** Y no se ve afectada.

---

### User Story 4 - Consulta de transacciones reutilizable por el agente (Priority: P4)

Como hook del agente, quiero consultar una transacción por su identificador directamente en
los datos del core, para obtener su monto y su titular reales sin depender del argumento que
envía el modelo.

**Why this priority**: es el prerrequisito de la garantía de la regla del umbral (issue #9);
la constitución exige que el monto venga del core.

**Independent Test**: consultar por identificador una transacción existente y una
inexistente.

**Acceptance Scenarios**:

1. **Given** el identificador de una transacción existente, **When** se consulta, **Then** se
   obtienen su monto, fecha, comercio, país, tarjeta y cliente titular.
2. **Given** un identificador inexistente, **When** se consulta, **Then** el resultado indica
   claramente que no existe, sin confundirse con un error transitorio.
3. **Given** la consulta, **When** la usa el agente, **Then** obtiene exactamente los mismos
   datos que verían las herramientas del core (una sola fuente de verdad).

---

### User Story 5 - Servidor ejecutable y registrado (Priority: P5)

Como desarrollador, quiero arrancar el servidor `core-bancario` con un comando y que Claude
Code lo conozca como servidor MCP del proyecto, para tener los dos servidores MCP que pide el
enunciado y una base donde agregar las herramientas.

**Why this priority**: es el esqueleto ejecutable; sus herramientas llegan en #5 a #7.

**Independent Test**: arrancar el servidor y comprobar que responde como servidor MCP; abrir
una sesión del asistente y ver el servidor registrado.

**Acceptance Scenarios**:

1. **Given** el proyecto instalado, **When** se ejecuta el comando de arranque, **Then** el
   servidor queda escuchando como servidor MCP por entrada y salida estándar.
2. **Given** la configuración MCP del proyecto, **When** se abre una sesión del asistente,
   **Then** `core-bancario` aparece registrado junto al servidor de GitHub, sin credenciales.

---

### User Story 6 - Ajustes heredados de los guardrails (Priority: P6)

Como desarrollador, quiero cerrar los pendientes que dejó la revisión del issue #3, para que
la convención de herramientas, los tests del control de datos y los mensajes del CI queden
consistentes antes de escribir las herramientas.

**Why this priority**: son ajustes menores; se hacen aquí porque este ticket define el
contrato de errores y los datos de tarjetas.

**Independent Test**: revisar la convención de herramientas y ejecutar los tests del control
de datos y del modo de revisión del CI.

**Acceptance Scenarios**:

1. **Given** la convención de herramientas MCP, **When** se lee, **Then** la regla de
   reintento coincide con el contrato de errores de esta spec.
2. **Given** una tarjeta válida escrita en formato 4-6-5, **When** el control de datos la
   revisa, **Then** la detecta (con un test que lo pruebe).
3. **Given** un diff donde se borra un archivo con un dato con forma real, **When** el CI lo
   revisa, **Then** no reporta falsamente un archivo llamado "/dev/null" (las líneas borradas
   no cuentan).

---

### Edge Cases

- **Cambio de día durante la ejecución**: las fechas relativas se calculan una vez por carga
  de datos respecto de un "hoy" que se puede fijar, para que los tests sean deterministas.
- **"Ayer" en fin de mes o de año**: el cobro de ayer cae correctamente el 31 o el 1.
- **Monto exactamente en el umbral ($500.000)**: los datos incluyen un cobro de ese monto
  para que el issue #9 pueda probar el borde.
- **Tarjeta bloqueada**: los datos incluyen al menos una tarjeta ya bloqueada, para que el
  issue #7 pueda probar el bloqueo repetido.
- **Falla configurada con número cero o negativo**: se trata como configuración inválida.
- **Archivo de datos corrupto o ausente**: el core falla al arrancar con un mensaje claro,
  no responde con datos vacíos.
- **Datos con forma real**: el control de datos del issue #3 impide escribirlos y el CI los
  detecta en el diff.

## Requirements *(mandatory)*

### Functional Requirements

**Contrato de errores**

- **FR-001**: Toda respuesta del core MUST tener la forma de éxito (`ok` verdadero y datos) o
  de error (`ok` falso con tipo, código, mensaje y reintentable).
- **FR-002**: El tipo de error MUST ser uno de: `transitorio`, `validacion`, `negocio`,
  `permiso`.
- **FR-003**: `reintentable` MUST ser verdadero para `transitorio` y falso para los otros
  tres tipos. (Resuelve el pendiente heredado: se adopta la regla de la convención de
  herramientas.)
- **FR-004**: Cada error MUST tener un código estable en mayúsculas (p. ej.
  `FALLA_TRANSITORIA`) y un mensaje en español comprensible para el agente.
- **FR-005**: Una búsqueda sin resultados MUST ser una respuesta exitosa con lista vacía.

**Datos ficticios**

- **FR-006**: Los datos MUST vivir en archivos locales versionados: clientes, tarjetas,
  transacciones y políticas.
- **FR-007**: Las tarjetas MUST guardarse solo con sus últimos 4 dígitos; los documentos con
  formato `CC-FIC-NNNN`.
- **FR-008**: Las fechas de las transacciones MUST expresarse como días hacia atrás respecto
  de la fecha de ejecución y resolverse al cargar, con un "hoy" que se pueda fijar.
- **FR-009**: Los datos MUST incluir: el cliente con tarjeta terminada en 4821 y sus dos
  cobros de ayer ($180.000 y $1.250.000); dos clientes con el mismo nombre; un cobro en el
  exterior de más de 90 días; un cobro de exactamente $500.000; una tarjeta ya bloqueada.
- **FR-010**: Cada cliente MUST tener un dato adicional de verificación, distinto de los de
  búsqueda, que el issue #5 usará para verificar identidad.
- **FR-011**: La política MUST declarar el límite de días para disputar cobros en el exterior
  (90 días).
- **FR-012**: Datos ausentes o mal formados MUST impedir el arranque con un mensaje claro.

**Fallas transitorias**

- **FR-013**: Una variable de entorno MUST permitir configurar qué operación falla y cuántas
  veces; las primeras N llamadas a esa operación devuelven un error transitorio reintentable.
- **FR-014**: Sin configuración, ninguna operación falla por inyección.
- **FR-015**: Una configuración inválida (formato incorrecto, número no positivo) MUST
  informarse al arrancar.
- **FR-016**: El mecanismo MUST poder aplicarse a cualquier operación del core por su nombre,
  incluidas las herramientas que lleguen en #5 a #7.

**Consulta reutilizable**

- **FR-017**: MUST existir una consulta de transacción por identificador que devuelva monto,
  fecha, comercio, país, tarjeta y cliente titular, y que indique sin ambigüedad cuando el
  identificador no existe.
- **FR-018**: Esa consulta MUST usar la misma fuente de datos que las herramientas del core.

**Servidor**

- **FR-019**: El servidor `core-bancario` MUST arrancar con un único comando y comunicarse
  como servidor MCP por entrada y salida estándar.
- **FR-020**: El servidor MUST estar registrado en la configuración MCP del proyecto sin
  credenciales.

**Ajustes heredados**

- **FR-021**: La convención de herramientas MCP MUST coincidir con FR-003.
- **FR-022**: El control de datos MUST tener un test que detecte una tarjeta válida en
  formato 4-6-5, generada al correr.
- **FR-023**: El modo de revisión de diffs MUST no atribuir hallazgos a "/dev/null" (archivos
  borrados).

### Key Entities

- **Cliente**: identificador, nombre completo, documento ficticio (`CC-FIC-NNNN`), dato de
  verificación, tarjetas.
- **Tarjeta**: identificador, últimos 4 dígitos, cliente titular, estado (activa o
  bloqueada).
- **Transacción**: identificador, tarjeta, fecha (relativa a la ejecución), monto en pesos
  ficticios, comercio, país, estado.
- **Política**: reglas de cobertura de disputas, en particular el límite de días para cobros
  en el exterior.
- **Respuesta del core**: éxito con datos, o error con tipo, código, mensaje y reintentable.
- **Configuración de fallas**: operación objetivo y número de fallas restantes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los casos de prueba obligatorios que requieren datos (mensaje de
  ejemplo, dos clientes con el mismo nombre, cobro no cubierto) encuentran sus datos con
  cualquier fecha de ejecución, incluidos fin de mes y fin de año.
- **SC-002**: Con una falla configurada de N veces, exactamente las primeras N llamadas
  fallan como transitorias y la N+1 tiene éxito, en el 100% de las ejecuciones.
- **SC-003**: El 100% de los errores de los cuatro tipos cumplen el contrato y la regla de
  reintento.
- **SC-004**: Cero datos con forma de tarjeta o documento real en los archivos del core
  (verificado por el control de datos y el CI).
- **SC-005**: El servidor arranca y queda disponible en menos de 5 segundos.
- **SC-006**: La consulta por identificador devuelve el monto correcto para el 100% de las
  transacciones de los datos.

## Assumptions

- **Regla de reintento**: se adopta "reintentable solo para transitorio" (FR-003). Es
  coherente con la razón del principio V (el agente decide por la estructura del error) y
  ningún error de validación, negocio o permiso se corrige reintentando igual.
- **Dato de verificación**: un dato ficticio adicional por cliente (p. ej. año de nacimiento
  ficticio); su uso concreto lo define el issue #5.
- **Sin herramientas todavía**: el servidor arranca sin herramientas de negocio; la
  inyección de fallas se prueba con operaciones de prueba y se aplicará a las herramientas de
  #5 a #7.
- **Consulta reutilizable**: el agente la usará desde el mismo repositorio (mismo proyecto
  Python); el mecanismo exacto (importación directa o vía el servidor) lo decide el plan.
- **Montos** en pesos colombianos ficticios, sin decimales.
- En esta rama también se marcan las tareas T036 y T037 del issue #3, como se acordó.
- Fuera de alcance: las herramientas de negocio (issues #5 a #7) y el uso de los datos por el
  agente (issues #8 en adelante).
