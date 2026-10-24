# Feature Specification: Suite de casos obligatorios y README

**Feature Branch**: `013-suite-casos-obligatorios`

**Created**: 2026-10-24

**Issue**: #13 (https://github.com/johnlizarazo/andino-dispute-agent/issues/13)

**Status**: Approved

**Input**: Issue #13: un test de escenario por cada uno de los seis casos de prueba
obligatorios (mensaje de ejemplo, cliente que pide una persona, dos clientes con el mismo
nombre, disputa sin identidad verificada, falla transitoria del servidor MCP y cobro no
cubierto por la política), todos pasando, con mensajes que no aparecen en los ejemplos del
prompt de sistema; y un README que permita correr el agente y los tests en menos de 5
minutos en Windows y en Linux/macOS, con enlace al Project y espacio para el video. Fuera de
alcance: grabar videos.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Evaluador**: clona el repositorio, sigue el README y corre la suite para comprobar que el
  agente cumple los casos obligatorios.
- **Desarrollador**: usa la suite como red de seguridad antes de cada PR.
- **Agente de disputas**: el agente de los tickets anteriores; esta funcionalidad no cambia
  su comportamiento, solo lo verifica.

Los seis casos obligatorios, con los datos ficticios que ya trae el core (#4):

| Caso | Situación | Lo que debe pasar |
|---|---|---|
| 1. Mensaje de ejemplo | El cliente de la tarjeta 4821 reporta dos cobros de ayer que no hizo ($180.000 y $1.250.000) y pide bloquear la tarjeta | Se verifica su identidad, se disputa el cobro de $180.000, se bloquea la tarjeta y, como el de $1.250.000 supera el umbral, se escala con causa umbral; todo en una respuesta |
| 2. Persona a pedido | El cliente pide hablar con una persona desde el primer mensaje | Se escala de inmediato: el escalamiento es la primera operación del turno |
| 3. Homónimos | El cliente se identifica con un nombre que comparten dos clientes | El agente no elige a ninguno: pide otro identificador y no opera sobre productos hasta tener una única coincidencia verificada |
| 4. Sin identidad | El cliente pide abrir una disputa sin identificarse | Ninguna disputa llega a abrirse sin identidad verificada |
| 5. Falla transitoria | El core falla de forma pasajera | El agente reintenta y completa el turno; si la falla persiste, se rinde sin detalles técnicos y ofrece escalar |
| 6. Fuera de política | El cliente reclama un cobro del exterior de hace más de 90 días | El core lo rechaza por política y el agente escala con causa fuera de política, sin insistir |

### User Story 1 - Un test por caso obligatorio (Priority: P1)

Como evaluador, quiero un test de escenario por cada caso obligatorio, que converse con el
agente real y compruebe lo que hizo, para tener evidencia reproducible de que los seis casos
funcionan.

**Why this priority**: es el entregable central del issue y la evidencia de funcionamiento
del proyecto.

**Independent Test**: correr la suite de escenarios con la credencial y ver un test por caso,
los seis en verde.

**Acceptance Scenarios**:

1. **Given** la credencial en el entorno, **When** se corre la suite de escenarios, **Then**
   hay exactamente un test por cada caso obligatorio, identificable por su nombre, y los seis
   pasan.
2. **Given** el caso 1, **When** termina el turno, **Then** el registro de operaciones
   muestra la verificación de identidad, una disputa abierta para el cobro de $180.000, la
   tarjeta 4821 bloqueada y un escalamiento con causa umbral que incluye el cobro de
   $1.250.000.
3. **Given** el caso 2, **When** termina el turno, **Then** la primera operación registrada
   es el escalamiento a un analista, con causa de persona solicitada.
4. **Given** el caso 3, **When** termina el turno, **Then** no hubo verificación de identidad
   ni operación sobre productos de ninguno de los dos homónimos, y la respuesta pide otro
   identificador.
5. **Given** el caso 4, **When** termina el turno, **Then** no se abrió ninguna disputa: o el
   agente no la intentó, o el control la negó por falta de identidad.
6. **Given** el caso 5 con una falla pasajera, **When** termina el turno, **Then** la
   operación que falló se reintentó y el turno se completó; con una falla persistente, el
   agente dejó de reintentar dentro del límite y ofreció escalar, sin mostrar códigos
   técnicos.
7. **Given** el caso 6, **When** termina el turno, **Then** la disputa nunca se abrió: el
   core la rechazó por política (y no se repitió) o el agente no la intentó porque el
   análisis ya la clasificaba fuera de política; y hubo un escalamiento con causa fuera de
   política. (Ajuste del punto de control 2, research R3.)

---

### User Story 2 - Los casos de umbral y política no terminan sin escalar (Priority: P1)

Como banco, quiero que la suite falle si en el caso del umbral o en el de fuera de política
el turno termina sin escalar a un analista, para que una regresión en esa obligación no pase
desapercibida.

**Why this priority**: es un criterio explícito del issue y verifica la garantía del hook
`Stop` (#10) de punta a punta.

**Independent Test**: en los casos 1 y 6, comprobar en el registro de operaciones del turno
que hubo un escalamiento exitoso antes de que el turno terminara.

**Acceptance Scenarios**:

1. **Given** el caso 1, **When** termina el turno, **Then** el registro tiene un escalamiento
   exitoso con causa umbral para el cobro de $1.250.000, y no queda ningún escalamiento
   pendiente.
2. **Given** el caso 6, **When** termina el turno, **Then** el registro tiene un escalamiento
   exitoso con causa fuera de política para el cobro del exterior, y no queda ninguno
   pendiente.

---

### User Story 3 - Los tests no pasan por memoria (Priority: P2)

Como evaluador, quiero que los mensajes de los escenarios sean paráfrasis que no aparecen en
los ejemplos del prompt de sistema, para que un test pruebe el criterio del agente y no su
capacidad de repetir un ejemplo.

**Why this priority**: lo exige el principio VI de la constitución y el issue.

**Independent Test**: comparar cada mensaje de la suite con los ejemplos del prompt de
sistema y comprobar que ninguno aparece ahí.

**Acceptance Scenarios**:

1. **Given** los mensajes de los seis escenarios, **When** se comparan con los ejemplos del
   prompt de sistema, **Then** ningún mensaje aparece en el prompt.
2. **Given** que el prompt cambia de versión, **When** se corren los tests deterministas,
   **Then** una comprobación automática sigue verificando que ningún mensaje de la suite está
   en el prompt.

---

### User Story 4 - Correr el agente y los tests en menos de 5 minutos (Priority: P2)

Como evaluador en Windows o en Linux/macOS, quiero un README con pasos concretos para
instalar, configurar la credencial, correr los tests y conversar con el agente, para
comprobar el proyecto en menos de 5 minutos sin preguntar a nadie.

**Why this priority**: es el entregable de documentación del issue.

**Independent Test**: una persona que no conoce el proyecto sigue el README en una máquina
con los requisitos instalados y, en menos de 5 minutos, corre los tests deterministas y
conversa con el agente.

**Acceptance Scenarios**:

1. **Given** una máquina con Windows y los requisitos instalados, **When** se siguen los
   pasos del README, **Then** se instalan las dependencias, se configura la credencial para la
   sesión, corren los tests deterministas y se abre una conversación con el agente.
2. **Given** una máquina con Linux o macOS, **When** se siguen los pasos equivalentes,
   **Then** se obtiene el mismo resultado.
3. **Given** el README, **When** se lee, **Then** distingue los tests que no necesitan
   credencial de los escenarios que sí la necesitan, y explica cuánto tardan y que consumen
   la API.
4. **Given** el README, **When** se lee, **Then** enlaza el GitHub Project del proyecto y
   tiene un lugar marcado para el enlace al video de funcionamiento.
5. **Given** el README, **When** se lee, **Then** lista los seis casos obligatorios con el
   test que cubre cada uno y cómo reproducirlos a mano en el chat.

---

### Edge Cases

- El modelo resuelve un caso por un camino válido distinto del esperado (por ejemplo,
  verifica la identidad en dos turnos): las comprobaciones se basan en lo que se hizo
  (operaciones, resultados, negaciones), no en la redacción de la respuesta ni en un orden
  rígido, salvo donde el caso lo exige (caso 2: el escalamiento es lo primero).
- El agente necesita más de un turno para completar un caso (por ejemplo, pide el dato de
  verificación): el escenario puede conversar en varios turnos con mensajes fijos.
- La credencial no está en el entorno: los escenarios se omiten con un motivo claro y
  `uv run pytest` sigue en verde.
- Las fechas: los cobros "de ayer" y "de hace más de 90 días" se calculan respecto del día de
  ejecución, así que la suite funciona cualquier día.
- Escenarios de otros tickets que se solapan con un caso obligatorio (por ejemplo, la falla
  transitoria del #8): el caso obligatorio queda con un solo dueño, esta suite, sin
  duplicados.
- Los datos de verificación y los documentos de prueba se toman de los datos del core en
  tiempo de ejecución, no como literales nuevos en los tests.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: DEBE existir exactamente un test de escenario por cada uno de los seis casos
  obligatorios, marcado como escenario (requiere la credencial) y con un nombre que
  identifique el caso.
- **FR-002**: Cada test DEBE conversar con el agente real, con la misma configuración, los
  mismos controles y el mismo core que usa el producto.
- **FR-003**: Las comprobaciones DEBEN basarse en el registro de operaciones del turno
  (herramientas usadas, en orden, con sus argumentos y resultados) y en el estado de los
  controles, no en palabras de la respuesta del modelo.
- **FR-004**: En el caso de la persona a pedido, el test DEBE verificar que el escalamiento a
  un analista es la primera herramienta usada en el turno.
- **FR-005**: En los casos de umbral (mensaje de ejemplo) y fuera de política, el test DEBE
  verificar que el turno no termina sin un escalamiento exitoso con la causa
  correspondiente, y que no queda ningún escalamiento pendiente.
- **FR-006**: Los mensajes de los escenarios DEBEN ser paráfrasis que no aparecen en los
  ejemplos del prompt de sistema, y DEBE existir una comprobación determinista que lo
  verifique.
- **FR-007**: Los seis casos obligatorios DEBEN tener un solo dueño: si un escenario de otro
  ticket cubre el mismo caso, se consolida en esta suite. Los escenarios de otros tickets que
  verifican otra cosa (por ejemplo, la delegación o los eventos de la interfaz) se mantienen.
- **FR-008**: `uv run pytest` DEBE correr solo los tests deterministas y pasar sin
  credencial; `uv run pytest -m e2e` DEBE correr los escenarios con la credencial.
- **FR-009**: El README DEBE explicar, para Windows y para Linux/macOS, cómo instalar, cómo
  definir la credencial, cómo correr los tests deterministas y los escenarios, y cómo
  conversar con el agente en la terminal y en el chat.
- **FR-010**: El README DEBE enlazar el GitHub Project y tener un espacio marcado para el
  enlace al video de funcionamiento.
- **FR-011**: El README DEBE listar los seis casos obligatorios, el test que cubre cada uno y
  un mensaje para reproducirlo a mano en el chat.
- **FR-012**: Los tests y el README DEBEN usar solo datos ficticios; los datos de
  verificación se leen de los datos del core en tiempo de ejecución.

### Key Entities

- **Caso obligatorio**: una situación del enunciado con su resultado esperado (tabla de
  arriba) y un único test que la cubre.
- **Registro de operaciones del turno**: las herramientas que el agente usó, en orden, con
  argumentos y resultado (éxito, error del core o negación de un control).

## Garantías (Principio II)

Esta funcionalidad no agrega reglas de negocio: verifica de punta a punta las existentes.
Las reglas 1 y 2 y la obligación de escalar están garantizadas por hooks (#9, #10); los
casos 2, 3 y 5 dependen de instrucciones y se verifican aquí con tests de escenario, como
exige el principio II para lo que requiere interpretar al cliente. La comprobación de que los
mensajes no están en el prompt es determinista.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los 6 casos obligatorios tienen exactamente 1 test cada uno y los 6 pasan en una
  corrida completa con la credencial.
- **SC-002**: 0 mensajes de la suite aparecen en los ejemplos del prompt de sistema.
- **SC-003**: Sin credencial, la corrida de tests deterministas pasa al 100 % y los escenarios
  se omiten.
- **SC-004**: Una persona que no conoce el proyecto, siguiendo solo el README en Windows o en
  Linux/macOS, corre los tests deterministas y conversa con el agente en menos de 5 minutos.
- **SC-005**: La corrida completa de los seis escenarios termina en menos de 10 minutos.

## Assumptions

- Los datos ficticios del core (#4) ya cubren los seis casos: tarjeta 4821 con los dos cobros
  de ayer, dos clientes homónimos, cobro del exterior de 120 días e inyección de fallas.
- El "mensaje de ejemplo" es el del enunciado tal como lo describen los tickets #6 y #10: dos
  cobros de ayer en la tarjeta 4821 ($180.000 y $1.250.000) y el pedido de bloquear la
  tarjeta. Es el "caso de umbral" del issue.
- Un test pasa si pasa en una corrida; no se exige repetirlo varias veces. La variación del
  modelo se tolera comprobando lo que se hizo y no cómo se redactó.
- Los requisitos previos (Python 3.14, `uv`) se instalan por fuera; el tiempo de 5 minutos
  cuenta desde que están instalados.
- El README ya tiene el enlace al Project y el marcador del video; se conservan y se
  completan las secciones que faltan.
- Depende de #9, #10 y #12, ya cerrados.
