# Feature Specification: Subagente `analista-transacciones`

**Feature Branch**: `011-subagente-analista-transacciones`

**Created**: 2026-10-24

**Issue**: #11 (https://github.com/johnlizarazo/andino-dispute-agent/issues/11)

**Status**: Approved

**Input**: Issue #11: el agente de disputas delega en un subagente `analista-transacciones` el
análisis de los cobros de un producto, pasándole el contexto de forma explícita (el subagente
no ve la conversación). El subagente solo puede consultar transacciones y devuelve una
clasificación por transacción. Las reglas de identidad verificada y del umbral siguen
aplicando a todo lo que haga.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Agente de disputas** (principal): conversa con el cliente y decide cuándo delegar.
- **Subagente `analista-transacciones`**: recibe solo el contexto que le pasa el principal,
  consulta los cobros y los clasifica; no conversa con el cliente ni opera sobre productos.
- **Controles del agente** (hooks): autorizan o niegan la delegación y cada consulta del
  subagente con las mismas reglas que al principal.
- **Cliente ficticio**: reporta uno o varios cobros que no reconoce.

### User Story 1 - Delegar el análisis con contexto explícito (Priority: P1)

Como agente de disputas, quiero pasarle al subagente el cliente verificado, el producto, el
rango de fechas y los montos que reporta el cliente, para que analice los cobros sin acceso a
la conversación.

**Why this priority**: es el requisito del issue (al menos un subagente con contexto
explícito).

**Independent Test**: con un cliente verificado, delegar el análisis de su tarjeta con un
rango y montos reportados, y comprobar que el subagente recibe exactamente ese contexto (y
nada de la conversación) y devuelve la clasificación.

**Acceptance Scenarios**:

1. **Given** un cliente verificado que reporta cobros que no reconoce, **When** el agente
   delega el análisis, **Then** la delegación lleva el cliente verificado, los últimos 4 de la
   tarjeta, el rango de fechas y los montos reportados, en un formato estructurado.
2. **Given** una delegación a la que le falta alguno de esos datos o con un formato que no se
   puede leer, **When** el agente intenta delegar, **Then** se niega con una razón que dice qué
   falta.
3. **Given** el subagente, **When** se revisa su definición, **Then** solo recibe el contexto
   de la delegación: no ve la conversación con el cliente.

---

### User Story 2 - El subagente solo consulta (Priority: P2)

Como banco, quiero que el subagente solo pueda consultar transacciones, para que analizar no
signifique poder disputar, bloquear ni escalar.

**Why this priority**: limita el daño posible de un componente que no conversa con el
cliente.

**Independent Test**: revisar la definición del subagente: su única herramienta es la
consulta de transacciones.

**Acceptance Scenarios**:

1. **Given** la definición del subagente, **When** se revisa, **Then** su única herramienta es
   `consultar_transacciones`; no tiene herramientas propias del motor ni las demás del core.
2. **Given** el agente principal, **When** se revisa su configuración, **Then** la única
   herramienta nueva que se le habilita es la de delegación, y solo para este subagente.

---

### User Story 3 - Las reglas 1 y 2 siguen aplicando al subagente (Priority: P3)

Como banco, quiero que la identidad verificada y el umbral se cumplan también en lo que haga el
subagente, para que delegar no abra una vía para saltarse las reglas.

**Why this priority**: es un criterio del issue y la garantía central del proyecto.

**Independent Test**: sin cliente verificado, intentar delegar y comprobar que se niega; con
un cliente verificado, comprobar que una consulta del subagente sobre otro cliente se niega
igual que la del principal; con la API, comprobar que los controles reciben las llamadas del
subagente.

**Acceptance Scenarios**:

1. **Given** una conversación sin cliente verificado, **When** el agente intenta delegar,
   **Then** se niega con la razón de verificar primero la identidad.
2. **Given** un cliente verificado, **When** la delegación indica otro cliente, **Then** se
   niega sin revelar datos de ese cliente.
3. **Given** una delegación autorizada, **When** el subagente consulta transacciones, **Then**
   la consulta pasa por los mismos controles de identidad y titularidad que las del principal.
4. **Given** una clasificación "disputable" para un cobro sobre el umbral (por un error del
   subagente), **When** el principal intenta disputarlo, **Then** el control del umbral lo
   niega igual: la clasificación no decide.

---

### User Story 4 - Clasificación por transacción (Priority: P4)

Como agente de disputas, quiero recibir, por cada cobro analizado, si es disputable, si supera
el umbral o si está fuera de política, para decidir qué disputar y qué escalar.

**Why this priority**: es el resultado que pide el issue; su valor es orientar al principal.

**Independent Test**: con la API, delegar el análisis de la tarjeta 4821 de CLI-001 con el
rango de ayer y comprobar que el cobro de $180.000 sale disputable y el de $1.250.000 sobre
el umbral; con la tarjeta 3344 de CLI-004, que el cobro del exterior de 120 días sale fuera de
política.

**Acceptance Scenarios**:

1. **Given** la respuesta del subagente, **When** el principal la recibe, **Then** trae, por
   cada transacción, su identificador, monto, fecha y una clasificación entre disputable,
   sobre umbral y fuera de política, con una razón breve.
2. **Given** montos reportados por el cliente, **When** el subagente analiza, **Then** indica
   qué transacciones coinciden con esos montos y cuáles montos reportados no aparecen.
3. **Given** que la consulta falla o no hay cobros en el rango, **When** el subagente responde,
   **Then** lo dice sin inventar transacciones.
4. **Given** la política del banco, **When** el subagente clasifica, **Then** usa el umbral y
   los plazos vigentes de la política (no valores escritos a mano).

---

### User Story 5 - Ajustes heredados del #10 (Priority: P5)

Como desarrollador, quiero cerrar las tareas pendientes y los no bloqueantes de las revisiones
del #10, para no arrastrarlos.

**Why this priority**: son correcciones menores de forma y cobertura.

**Independent Test**: correr la suite determinista y revisar las tareas del #10.

**Acceptance Scenarios**:

1. **Given** las tareas del #10, **When** se revisan, **Then** T022 y T023 están marcadas y el
   texto de T006 nombra el código real del core.
2. **Given** los controles de cierre de turno y de mensaje nuevo, **When** reciben entradas mal
   formadas, **Then** no lanzan, con tests que lo cubren.

---

### Edge Cases

- **Delegación sin montos reportados**: válida si la lista está vacía (el cliente no recuerda
  montos); el subagente clasifica todos los cobros del rango.
- **Rango de fechas inválido o invertido**: la delegación se niega por formato; si llega al
  core, el core también lo rechaza.
- **El subagente intenta otra herramienta**: no la tiene; no hay forma de usarla.
- **Varias delegaciones en la misma conversación**: cada una se controla por separado.
- **El cliente verificado cambia entre delegaciones**: se controla contra el verificado del
  momento de cada delegación.
- **Falla de los controles al leer la delegación**: niegan (falla cerrada).
- **El subagente responde con un formato que no se puede leer**: el principal no lo trata como
  clasificación válida y sigue con las herramientas normales (consulta propia o escalar).

## Requirements *(mandatory)*

### Functional Requirements

**Definición y delegación**

- **FR-001**: El agente MUST tener un subagente `analista-transacciones` cuya única herramienta
  sea `consultar_transacciones` y que solo reciba el contexto de la delegación.
- **FR-002**: El agente principal MUST poder delegar en ese subagente y en ningún otro; no se le
  habilitan otras herramientas propias del motor.
- **FR-003**: La delegación MUST llevar un bloque estructurado con cliente, últimos 4 de la
  tarjeta, fecha inicial, fecha final y montos reportados (lista, puede estar vacía).

**Reglas 1 y 2 sobre el subagente (deterministas)**

- **FR-004**: Antes de delegar, los controles MUST negar si no hay cliente verificado, si el
  cliente del bloque no es el verificado, o si el bloque falta, no se puede leer o tiene datos
  con formato inválido; la razón dice qué corregir y no revela datos de otros clientes.
- **FR-005**: Las consultas del subagente MUST pasar por los mismos controles de identidad y
  titularidad que las del principal (comprobado con la API).
- **FR-006**: El subagente MUST NOT poder disputar, bloquear ni escalar; la regla del umbral
  sigue aplicando a las disputas del principal aunque la clasificación diga otra cosa.

**Clasificación (orientativa)**

- **FR-007**: El subagente MUST devolver, por transacción, identificador, monto, fecha,
  clasificación (disputable, sobre umbral, fuera de política) y una razón breve, más los montos
  reportados que no encontró, en un formato estructurado.
- **FR-008**: Las instrucciones del subagente MUST incluir el umbral y los plazos tomados de la
  política del banco.
- **FR-009**: El prompt del principal MUST orientar cuándo delegar (cliente verificado que
  reporta cobros a analizar) y cómo usar la clasificación (disputar lo disputable, escalar lo
  demás), recordando que los controles deciden.

**Heredados del #10**

- **FR-010**: Los ajustes de US5.

### Key Entities

- **Contexto de delegación**: cliente, últimos 4, fecha inicial, fecha final, montos
  reportados.
- **Clasificación de transacción**: identificador, monto, fecha, clasificación, razón.
- **Resultado del análisis**: lista de clasificaciones y montos reportados no encontrados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de las delegaciones sin cliente verificado, con otro cliente o con el
  contexto incompleto se niegan antes de llegar al subagente.
- **SC-002**: En la verificación con la API, el 100% de las consultas del subagente pasan por
  los controles de identidad y titularidad.
- **SC-003**: En la verificación con la API, con el mensaje de ejemplo el subagente clasifica
  el cobro de $180.000 como disputable y el de $1.250.000 como sobre umbral, y con el cobro
  del exterior de 120 días, como fuera de política.
- **SC-004**: El subagente tiene exactamente una herramienta disponible.
- **SC-005**: Ninguna disputa sobre el umbral se inicia aunque la clasificación la marque como
  disputable (los controles del #9 siguen decidiendo).

## Assumptions

- **Garantías por regla** (principio II):
  - Regla 1 sobre la delegación (cliente verificado y contexto completo): **garantizada por
    control determinista** sobre la delegación, que falla cerrado.
  - Regla 1 sobre las consultas del subagente: **garantizada por los controles existentes**
    del #9 (mismo nombre completo de herramienta); se verifica con la API que se disparan.
  - Regla 2: **imposible por diseño** para el subagente (no puede disputar) y **garantizada por
    control** para el principal (#9).
  - Que el subagente no vea la conversación: **por diseño** del mecanismo de subagentes (solo
    recibe el texto de la delegación).
  - Clasificación correcta: **orientada por instrucción** y verificada con la API; es una ayuda,
    no una garantía.
- **Formato del bloque**: un objeto estructurado (JSON) dentro del mensaje de delegación; el
  plan fija su forma exacta. Se elige un formato estructurado para que el control pueda
  verificarlo sin interpretar texto libre.
- **Política en las instrucciones**: umbral $500.000 y plazos de 90 días (exterior) y 120 días
  (nacional), leídos de los datos de la política al armar las opciones.
- **Modelo del subagente**: el mismo del principal salvo que el plan justifique otro.
- **Pendientes del #10**: un escalamiento pendiente no impide delegar (delegar no es cerrar el
  turno).
- En esta rama también se marcan T022 y T023 del #10.
