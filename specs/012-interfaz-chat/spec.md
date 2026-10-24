# Feature Specification: Interfaz de chat

**Feature Branch**: `012-interfaz-chat`

**Created**: 2026-10-24

**Issue**: #12 (https://github.com/johnlizarazo/andino-dispute-agent/issues/12)

**Status**: Approved

**Input**: Issue #12: una interfaz de chat donde se ven los mensajes del cliente y del agente
turno a turno, y donde los bloqueos, las disputas iniciadas, los escalamientos y las
negaciones de los controles se muestran como eventos claramente visibles, de modo que una
persona que no conoce el código entienda qué pasó. Arranca con un solo comando documentado.
Fuera de alcance: diseño visual.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Cliente ficticio**: escribe en el chat y lee las respuestas del agente.
- **Observador** (evaluador, analista o desarrollador): mira la conversación, sin conocer el
  código, para entender qué hizo el agente y por qué.
- **Agente de disputas**: el mismo agente de los tickets anteriores (ciclo agéntico, core
  bancario, controles y subagente); esta interfaz no cambia su comportamiento.

### User Story 1 - Conversar turno a turno en el chat (Priority: P1)

Como cliente, quiero escribir mis mensajes en una ventana de chat y ver la respuesta del agente
debajo de cada uno, para atender mi caso sin usar una terminal.

**Why this priority**: sin la conversación turno a turno no hay interfaz; es el mínimo viable.

**Independent Test**: arrancar la interfaz, enviar dos mensajes seguidos y comprobar que cada
mensaje del cliente aparece seguido de la respuesta del agente, en orden, y que el agente
recuerda lo dicho en el turno anterior.

**Acceptance Scenarios**:

1. **Given** la interfaz abierta, **When** el cliente envía un mensaje, **Then** el mensaje
   aparece en el historial como del cliente y, al terminar el turno, la respuesta aparece como
   del agente, debajo.
2. **Given** una conversación con turnos previos, **When** el cliente envía otro mensaje,
   **Then** el agente responde con el contexto de los turnos anteriores de la misma
   conversación (no empieza de cero).
3. **Given** una conversación nueva (otra pestaña o un reinicio del chat), **When** el cliente
   escribe, **Then** empieza una sesión independiente: no hereda la identidad verificada ni el
   historial de otra conversación.
4. **Given** un turno que termina sin respuesta normal (salvaguarda, falla temporal del
   servicio o error), **When** termina el turno, **Then** el cliente ve el mismo aviso
   comprensible que ya da la línea de comandos, sin trazas ni datos técnicos.

---

### User Story 2 - Ver los eventos importantes de la conversación (Priority: P2)

Como observador, quiero que el bloqueo de una tarjeta, la disputa iniciada, el escalamiento a
un analista y la negación de una operación por los controles aparezcan como eventos
destacados, separados del texto del agente, para saber qué pasó sin depender de lo que el
modelo diga.

**Why this priority**: es lo que distingue esta interfaz de la línea de comandos y es el
segundo criterio del issue.

**Independent Test**: en conversaciones que provoquen cada evento (bloqueo, disputa dentro
del umbral, disputa por encima del umbral con su escalamiento, operación sin identidad
verificada), comprobar que cada uno aparece como un evento visible con su resultado.

**Acceptance Scenarios**:

1. **Given** un cliente verificado que pide bloquear su tarjeta, **When** el bloqueo se
   completa, **Then** aparece un evento "Tarjeta bloqueada" con los últimos 4 dígitos.
2. **Given** una disputa dentro del umbral, **When** se inicia, **Then** aparece un evento
   "Disputa iniciada" con el identificador de la disputa, la transacción y el monto según el
   core.
3. **Given** un caso escalado (por pedido del cliente, por umbral o por política), **When** el
   escalamiento se registra, **Then** aparece un evento "Caso escalado a un analista" con el
   motivo y el identificador del caso.
4. **Given** una operación que los controles niegan (identidad no verificada, titular
   distinto, monto por encima del umbral, delegación inválida), **When** se niega, **Then**
   aparece un evento "Operación negada por control" con la operación y la razón en lenguaje
   claro.
5. **Given** una disputa que el core rechaza por política, **When** ocurre, **Then** aparece
   un evento que lo indica, para que se entienda por qué el agente escala a continuación.
6. **Given** un turno que termina con un escalamiento pendiente que no se pudo registrar,
   **When** termina, **Then** se muestra el aviso de escalamiento pendiente, generado por la
   interfaz y no por el modelo.
7. **Given** una operación que falla por un error del core (transitorio o de validación),
   **When** ocurre, **Then** se muestra como evento de falla distinguible de un éxito: nunca
   se presenta como completada una operación que no se completó.

---

### User Story 3 - Entender la conversación sin conocer el código (Priority: P2)

Como observador sin conocimiento del código, quiero que los eventos estén en el mismo orden
en que ocurrieron, junto al turno que los produjo y con nombres de negocio, para reconstruir
qué pasó leyendo solo el chat.

**Why this priority**: es el tercer criterio del issue; complementa la historia 2 con
legibilidad.

**Independent Test**: mostrar a una persona ajena al proyecto una conversación con un bloqueo
y un escalamiento por umbral, y pedirle que describa qué pasó; su descripción coincide con lo
ocurrido.

**Acceptance Scenarios**:

1. **Given** un turno con varias operaciones, **When** termina, **Then** los eventos aparecen
   dentro de ese turno, en el orden en que ocurrieron, antes o junto a la respuesta del agente.
2. **Given** cualquier evento, **When** se muestra, **Then** usa nombres de negocio
   ("Identidad verificada", "Disputa iniciada", "Caso escalado"), no nombres internos de
   herramientas, códigos de error crudos ni estructuras de datos.
3. **Given** la verificación de identidad, **When** resulta exitosa o fallida, **Then** se
   muestra como evento, porque explica por qué las operaciones posteriores se permiten o se
   niegan.
4. **Given** una delegación al subagente de análisis, **When** ocurre, **Then** se muestra
   como un paso de análisis visible, sin exponer el razonamiento interno del modelo.

---

### User Story 4 - Arrancar con un solo comando (Priority: P3)

Como desarrollador o evaluador, quiero arrancar la interfaz con un único comando documentado
en el README, para probarla sin pasos manuales adicionales.

**Why this priority**: es el cuarto criterio del issue; depende de que lo demás exista.

**Independent Test**: en un clon limpio con dependencias instaladas y la credencial en el
entorno, ejecutar el comando del README y conversar en el navegador.

**Acceptance Scenarios**:

1. **Given** el repositorio con dependencias instaladas y la credencial en el entorno,
   **When** se ejecuta el comando documentado, **Then** la interfaz queda disponible en el
   navegador y el core bancario arranca con ella.
2. **Given** que falta la credencial, **When** se abre el chat, **Then** se informa con un
   mensaje claro y no se atiende ningún mensaje (la comprobación ocurre al abrir cada
   conversación, no al arrancar el servidor).
3. **Given** que el core bancario no arranca, **When** se abre una conversación, **Then** el
   cliente ve un aviso claro y no se intenta atenderlo sin core.

---

### Edge Cases

- El cliente envía un mensaje mientras el turno anterior sigue en curso: no se mezclan
  respuestas; el nuevo mensaje se atiende cuando termina el anterior o se impide enviarlo
  hasta entonces.
- La sesión del agente se pierde a mitad de conversación: el cliente ve el aviso de que la
  conversación no puede continuar, como en la línea de comandos.
- Un turno con muchas operaciones (solicitudes múltiples): todos los eventos aparecen, cada
  uno una vez, sin duplicarse por reintentos del hook `Stop`.
- La respuesta de una herramienta no se puede interpretar: el evento se muestra como falla o
  se omite, pero nunca como éxito.
- El cliente cierra la pestaña: la sesión del agente se libera.
- Los eventos solo muestran datos ficticios y tarjetas como últimos 4 dígitos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La interfaz DEBE mostrar los mensajes del cliente y las respuestas del agente
  como un historial turno a turno, diferenciando quién habla.
- **FR-002**: Cada conversación DEBE tener su propia sesión de agente, con su propio estado de
  controles (identidad verificada, escalamientos pendientes); dos conversaciones no comparten
  estado.
- **FR-003**: La interfaz DEBE usar el mismo agente, opciones, controles y core bancario que
  la línea de comandos; no DEBE relajar, duplicar ni reemplazar ninguna regla de negocio.
- **FR-004**: La interfaz DEBE mostrar como eventos visibles, separados del texto del agente:
  verificación de identidad (éxito o fallo), tarjeta bloqueada, disputa iniciada, disputa
  rechazada por política, caso escalado, operación negada por control y falla de una
  operación.
- **FR-005**: Los eventos DEBEN derivarse de lo que realmente ocurrió (llamadas a herramientas,
  sus respuestas estructuradas y las decisiones de los controles), no del texto que redacta el
  modelo.
- **FR-006**: Cada evento DEBE indicar su resultado (éxito, negado, falla) y los datos de
  negocio que lo explican (últimos 4 de la tarjeta, identificador de disputa o caso, monto
  según el core, motivo o razón de la negación).
- **FR-007**: Los eventos DEBEN mostrarse en el orden en que ocurrieron, asociados al turno
  que los produjo.
- **FR-008**: Los eventos DEBEN usar lenguaje de negocio en español; no DEBEN exponer nombres
  internos de herramientas, trazas, códigos crudos ni estructuras de datos.
- **FR-009**: Los turnos que no terminan normalmente (salvaguarda, falla temporal, error,
  sesión perdida) y el escalamiento pendiente DEBEN producir los mismos avisos que la línea de
  comandos.
- **FR-010**: La interfaz DEBE arrancar con un único comando, documentado en el README, que
  también arranque el core bancario.
- **FR-011**: Si falta la credencial o el core no queda conectado, la interfaz DEBE informarlo
  con un mensaje claro al abrir la conversación y no atender sus mensajes.
- **FR-012**: La lógica que convierte lo ocurrido en un turno en eventos DEBE poder probarse
  de forma determinista, sin llamadas a la API.
- **FR-013**: La interfaz no DEBE mostrar ni registrar datos que no sean ficticios; las
  tarjetas solo como últimos 4 dígitos.

### Key Entities

- **Conversación**: una sesión de chat con su propio agente, estado de controles e historial.
- **Turno**: un mensaje del cliente, los eventos que produjo y la respuesta o aviso final.
- **Evento**: algo relevante que ocurrió en un turno; tiene tipo (identidad, bloqueo,
  disputa, rechazo por política, escalamiento, negación, falla), resultado y datos de negocio.

## Garantías (Principio II)

Esta funcionalidad no agrega reglas de negocio: las reglas 1 a 5 siguen garantizadas por los
hooks, el diseño de herramientas y el servidor, que la interfaz reutiliza sin cambios. Lo que
sí debe cumplirse (que un evento refleje lo ocurrido y no lo que dice el modelo) se garantiza
derivando los eventos de las llamadas y respuestas estructuradas, y se verifica con tests
deterministas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En los casos obligatorios del proyecto, el 100 % de los bloqueos, disputas
  iniciadas, escalamientos y negaciones por control aparecen como evento visible en el turno
  correspondiente.
- **SC-002**: Ningún evento se muestra como exitoso cuando la operación fue negada o falló
  (0 falsos éxitos en los tests deterministas).
- **SC-003**: Una persona que no conoce el código, al leer una conversación con un bloqueo y un
  escalamiento por umbral, describe correctamente qué pasó y por qué en menos de 2 minutos.
- **SC-004**: Desde un clon con dependencias instaladas y la credencial en el entorno, la
  interfaz queda lista para conversar con un solo comando, en menos de 1 minuto.
- **SC-005**: Ningún aviso ni evento muestra trazas, códigos crudos o nombres internos de
  herramientas.

## Assumptions

- La tecnología de la interfaz la fija la constitución (Chainlit); el issue la nombra
  explícitamente.
- El diseño visual (colores, estilos, marca) está fuera de alcance; basta con los elementos
  estándar del chat para diferenciar mensajes y eventos.
- La línea de comandos se mantiene; la interfaz es una segunda forma de conversar con el mismo
  agente.
- Es una herramienta de demostración local: un solo usuario, sin autenticación de usuarios ni
  persistencia del historial entre reinicios.
- La conversación usa los datos ficticios del core bancario y la credencial del entorno, como
  la línea de comandos.
- La respuesta del agente se muestra al terminar el turno; mostrarla en streaming es opcional.
- Depende de #8 (ciclo agéntico y conexión al MCP), ya cerrado; reutiliza también los
  controles de #9 y #10 y el subagente de #11.
