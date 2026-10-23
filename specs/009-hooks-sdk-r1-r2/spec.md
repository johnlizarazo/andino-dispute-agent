# Feature Specification: Hooks del SDK para R1 y R2

**Feature Branch**: `009-hooks-sdk-r1-r2`

**Created**: 2026-10-23

**Issue**: #9 (https://github.com/johnlizarazo/andino-dispute-agent/issues/9)

**Status**: Approved

**Input**: Issue #9: las reglas de identidad verificada (regla 1) y del umbral de $500.000
(regla 2) se hacen cumplir con controles deterministas en el agente, no con instrucciones en
el prompt. Caso de prueba: intento de iniciar una disputa sin identidad verificada.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Agente de disputas**: pide usar herramientas del core; no decide si puede.
- **Controles del agente** (hooks): registran quién está verificado en la conversación y
  autorizan o niegan cada operación sobre productos antes de que llegue al core.
- **Cliente ficticio**: se identifica y verifica antes de operar sobre sus productos.
- **Subagente** (issue #11): sus llamadas pasan por los mismos controles.

### User Story 1 - Sin identidad verificada no se opera sobre productos (Priority: P1)

Como banco, quiero que ninguna consulta, disputa ni bloqueo ocurra si en la conversación no se
verificó la identidad de un cliente, aunque el modelo lo intente, para cumplir la regla 1 sin
depender de que el modelo obedezca.

**Why this priority**: es la regla 1 de la constitución y el caso de prueba del issue.

**Independent Test**: sin verificación previa, pedir a los controles que autoricen una disputa
y comprobar que la niegan con una razón explicativa.

**Acceptance Scenarios**:

1. **Given** una conversación sin cliente verificado, **When** el agente intenta consultar
   cobros, iniciar una disputa o bloquear una tarjeta, **Then** la operación se niega antes de
   llegar al core, con una razón que indica verificar primero la identidad.
2. **Given** una verificación exitosa de un cliente, **When** después intenta operar sobre sus
   productos, **Then** la operación se autoriza (salvo lo que dicten la regla de titularidad o
   el umbral).
3. **Given** una verificación fallida, **When** intenta operar, **Then** se sigue negando: solo
   una verificación exitosa cuenta.
4. **Given** las herramientas exentas (buscar, verificar, escalar), **When** se usan sin
   verificación, **Then** se permiten.

---

### User Story 2 - Solo sobre productos del cliente verificado (Priority: P2)

Como banco, quiero que, aun con un cliente verificado, no se pueda operar sobre productos ni
transacciones de otra persona, para que verificar a un cliente no abra la puerta a los datos de
otro.

**Why this priority**: la regla 1 exige que la identidad corresponda al titular.

**Independent Test**: con CLI-001 verificado, pedir consultar o bloquear con otro cliente y
disputar una transacción de otro cliente; comprobar que se niega.

**Acceptance Scenarios**:

1. **Given** CLI-001 verificado, **When** el agente consulta o bloquea indicando otro cliente,
   **Then** se niega con una razón que no revela datos del otro cliente.
2. **Given** CLI-001 verificado, **When** intenta disputar una transacción cuyo titular es otro
   cliente, **Then** se niega.
3. **Given** una segunda verificación exitosa de otro cliente en la misma conversación, **When**
   opera, **Then** los controles toman al último cliente verificado como titular válido.

---

### User Story 3 - Disputas sobre el umbral se niegan antes del core (Priority: P3)

Como banco, quiero que una disputa por más de $500.000 se niegue en el agente, consultando el
monto real por la transacción, para cumplir la regla 2 aunque el modelo invente o ignore el
monto.

**Why this priority**: es la regla 2; el core ya la aplica como segunda defensa (#6).

**Independent Test**: con el titular verificado, pedir disputar el cobro de $1.250.000 y el de
exactamente $500.000; comprobar que el primero se niega y el segundo se autoriza.

**Acceptance Scenarios**:

1. **Given** el titular verificado, **When** intenta disputar una transacción de $1.250.000,
   **Then** se niega con una razón que indica que requiere un analista.
2. **Given** el titular verificado, **When** intenta disputar una transacción de exactamente
   $500.000, **Then** se autoriza.
3. **Given** que no se puede obtener el monto o el titular de la transacción (no existe, los
   datos no cargan o la consulta falla, incluida una falla inyectada), **When** intenta
   disputar, **Then** se niega (falla cerrado) con una razón explicativa.
4. **Given** cualquier error inesperado dentro de un control, **When** ocurre, **Then** la
   operación se niega; nunca se autoriza por omisión.

---

### User Story 4 - Las garantías no dependen del prompt (Priority: P4)

Como evaluador, quiero comprobar que, aunque el prompt de sistema se omita o diga lo
contrario, las operaciones prohibidas quedan bloqueadas, para demostrar que la regla no vive
en el prompt.

**Why this priority**: es el criterio que distingue un hook de una instrucción (principio II).

**Independent Test**: armar el agente sin prompt de sistema y comprobar que los controles
siguen negando la disputa sin verificación.

**Acceptance Scenarios**:

1. **Given** el agente configurado sin prompt de sistema, **When** se evalúa una disputa sin
   identidad verificada, **Then** se niega igual.
2. **Given** las herramientas sobre productos, **When** se revisa la configuración, **Then**
   los controles se aplican por el nombre completo de cada herramienta del core, de modo que
   también cubren las llamadas de un subagente.
3. **Given** los controles en su lugar, **When** se revisa la configuración, **Then**
   `consultar_transacciones`, `iniciar_disputa` y `bloquear_tarjeta` quedan habilitadas (ya no
   deshabilitadas como en el #8) y el prompt deja de indicar que no están disponibles.

---

### User Story 5 - Ajustes heredados de las revisiones del #8 (Priority: P5)

Como desarrollador, quiero cerrar los no bloqueantes de las revisiones del #8, para no
arrastrarlos.

**Why this priority**: uno de ellos evita sondear identificadores de transacción.

**Independent Test**: correr la suite determinista y revisar los artefactos del #8.

**Acceptance Scenarios**:

1. **Given** `escalar_a_analista` sin cliente (causa "persona solicitada"), **When** se envían
   transacciones, **Then** se rechaza con un error de validación: sin cliente no se indican
   transacciones, así no se puede saber si un identificador existe.
2. **Given** la línea de comandos, **When** el arranque se interrumpe con Ctrl+C o no se
   encuentra el motor del agente, **Then** termina sin traza (con tests que lo cubren).
3. **Given** el código y las tareas del #8, **When** se leen, **Then** la tarea T007 refleja
   las herramientas habilitadas, la anotación de tipo de la función del turno está completa y
   no hay líneas desproporcionadamente largas.

---

### Edge Cases

- **Argumentos mal formados** (sin `cliente_id`, sin `transaccion_id`, tipos incorrectos): se
  niega en el control; el core igual los rechazaría.
- **Varias herramientas sobre productos en el mismo paso**: cada una se evalúa por separado.
- **Verificación exitosa cuyo resultado no se puede leer**: no registra a nadie (falla
  cerrado).
- **Escalar tras una negación**: siempre permitido (exento); la obligación de escalar es del
  #10.
- **Fin de la conversación**: el cliente verificado se olvida; una nueva conversación empieza
  sin verificación.

## Requirements *(mandatory)*

### Functional Requirements

**Registro de identidad**

- **FR-001**: Tras cada `verificar_identidad` exitosa, los controles MUST registrar en la
  conversación el cliente verificado; una verificación fallida o ilegible MUST NOT registrar a
  nadie.
- **FR-002**: El cliente verificado MUST vivir solo mientras dure la conversación.

**Regla 1 (identidad y titularidad)**

- **FR-003**: Antes de `consultar_transacciones`, `iniciar_disputa` o `bloquear_tarjeta`, los
  controles MUST negar si no hay cliente verificado, con una razón que indique verificar la
  identidad primero.
- **FR-004**: MUST negar si el cliente indicado (consultar, bloquear) o el titular de la
  transacción según el core (disputar) no es el cliente verificado, sin revelar datos del otro
  cliente.
- **FR-005**: `buscar_cliente`, `verificar_identidad` y `escalar_a_analista` MUST quedar fuera
  de estos controles.

**Regla 2 (umbral)**

- **FR-006**: Antes de `iniciar_disputa`, los controles MUST obtener el monto real de la
  transacción desde los datos del core por su identificador y negar si supera $500.000;
  exactamente $500.000 MUST autorizarse. La razón MUST indicar que requiere un analista.

**Falla cerrada y alcance**

- **FR-007**: Si un control no puede obtener lo que necesita para decidir, o falla por
  cualquier motivo, MUST negar con una razón explicativa.
- **FR-008**: Los controles MUST aplicarse por el nombre completo de cada herramienta del core,
  de modo que cubran también las llamadas de subagentes.
- **FR-009**: Los controles MUST aplicarse aunque el prompt de sistema se omita.
- **FR-010**: Con los controles activos, el agente MUST habilitar las tres herramientas sobre
  productos y el prompt MUST dejar de indicar que no están disponibles (nueva versión).

**Heredados del #8**

- **FR-011**: Los tres ajustes de US5.

### Key Entities

- **Cliente verificado de la conversación**: identificador del último cliente verificado con
  éxito; vacío al empezar.
- **Decisión de control**: autorizar o negar, con una razón explicativa cuando se niega.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los intentos de consultar, disputar o bloquear sin identidad
  verificada se niegan antes de llegar al core.
- **SC-002**: El 100% de los intentos sobre productos o transacciones de otro cliente se niegan.
- **SC-003**: El 100% de las disputas sobre $500.000 se niegan en el agente y el 100% de las de
  exactamente $500.000 del titular verificado se autorizan.
- **SC-004**: Ante una falla para obtener los datos de la decisión, el 100% de las operaciones
  se niegan.
- **SC-005**: Los resultados de SC-001 a SC-004 son los mismos con o sin prompt de sistema.

## Assumptions

- **Garantías por regla** (principio II):
  - Regla 1 (identidad y titularidad): **garantizada por control determinista** en el agente,
    que falla cerrado. El core además valida que la tarjeta sea del cliente indicado (#6, #7).
  - Regla 2 (umbral): **garantizada por control determinista** en el agente con el monto del
    core, y el core la repite como segunda defensa (#6).
  - Escalar después de una negación: **fuera de alcance** (#10, hook `Stop`).
- **Datos para decidir**: los controles leen monto y titular de los mismos datos ficticios del
  core en el proceso del agente; monto y titular no cambian durante la conversación.
- **Falla inyectada en los controles**: la consulta de datos de los controles puede fallar a
  propósito, como el core, para probar la falla cerrada.
- **Último verificado**: si en la misma conversación se verifica con éxito a otro cliente, pasa
  a ser el titular válido (un solo cliente a la vez).
- **Razones de negación**: en español, útiles para que el agente explique o escale; nunca
  incluyen datos de otros clientes.
- En esta rama también se marcan T020 y T021 del #8.
