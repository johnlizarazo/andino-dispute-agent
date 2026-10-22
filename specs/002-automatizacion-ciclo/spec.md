# Feature Specification: Automatización del ciclo en GitHub

**Feature Branch**: `002-automatizacion-ciclo`

**Created**: 2026-10-22

**Status**: Draft

**Issue**: #2 (https://github.com/johnlizarazo/andino-dispute-agent/issues/2)

**Input**: Issue #2 "Automatización del ciclo en GitHub": el asistente toma tickets, los
mueve de estado, comenta avances y los cierra con el pull request sin intervención manual;
las decisiones de contenido pasan por puntos de control humanos.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Desarrollador**: decide qué ticket trabajar, revisa los artefactos en cada punto de
  control y fusiona el pull request.
- **Asistente de programación**: sesión de Claude Code que ejecuta los comandos del ciclo.
- **Revisor independiente**: subagente de solo lectura que no comparte la conversación de
  la sesión que escribió el código.
- **Evaluador**: reconstruye el avance del proyecto solo desde GitHub.

### User Story 1 - Tomar el siguiente ticket (Priority: P1)

Como desarrollador, quiero pedirle al asistente el siguiente ticket (o uno concreto) y que
él lo mueva a *In Progress*, comente el inicio, prepare la rama y genere la especificación
a partir del issue, para empezar a trabajar sin tocar GitHub a mano.

**Why this priority**: es el punto de entrada del ciclo; sin él, cada ticket arranca con
movimientos manuales y la trazabilidad depende de la memoria del desarrollador.

**Independent Test**: con el issue #3 en *Todo*, invocar el comando sin argumentos y
verificar en GitHub el cambio de estado y el comentario, y en el repositorio la rama y la
spec que enlaza el issue.

**Acceptance Scenarios**:

1. **Given** hay issues en *Todo*, **When** el desarrollador invoca el comando sin
   argumentos, **Then** el asistente elige el siguiente según la regla de selección
   (FR-002) y dice cuál eligió y por qué.
2. **Given** el desarrollador indica un número de issue, **When** invoca el comando,
   **Then** el asistente trabaja ese issue aunque no sea el siguiente.
3. **Given** el issue elegido, **When** el comando termina, **Then** el issue está en *In
   Progress*, tiene un comentario de inicio con la rama, existe la rama `NNN-slug` con su
   carpeta en `specs/`, y la `spec.md` enlaza el issue (`Issue: #N`).
4. **Given** la spec quedó escrita, **When** el comando termina, **Then** se detiene y
   presenta la spec para revisión; no ejecuta plan, tareas ni implementación.
5. **Given** el issue ya está en el Project (agregado automáticamente), **When** el
   comando lo mueve, **Then** actualiza el ítem existente sin duplicarlo.

---

### User Story 2 - Abrir el pull request tras una revisión independiente (Priority: P2)

Como desarrollador, quiero un comando que, antes de crear el pull request, haga revisar el
cambio por un revisor independiente, se detenga si hay bloqueantes y, si no los hay, cree
el pull request que cierra el issue, mueva el issue a *In Review* y deje un comentario con
lo especificado, lo decidido y lo pendiente.

**Why this priority**: cubre la necesidad de "revisión independiente antes del PR" y es la
mitad de la sincronización de estados; sin él, la revisión y el paso a *In Review* son
manuales (como pasó en el issue #1).

**Independent Test**: en una rama con un cambio que viola la spec, invocar el comando y
verificar que se detiene mostrando el bloqueante; corregirlo, invocarlo de nuevo y
verificar el PR, el estado y el comentario en GitHub.

**Acceptance Scenarios**:

1. **Given** una rama de ticket con cambios, **When** se invoca el comando, **Then** el
   revisor independiente analiza el diff contra la spec de la rama y reporta bloqueantes y
   no bloqueantes con su ubicación.
2. **Given** el revisor reporta al menos un bloqueante, **When** termina la revisión,
   **Then** el comando se detiene sin publicar nada y muestra los bloqueantes.
3. **Given** el revisor no reporta bloqueantes, **When** el comando continúa, **Then** se
   publica la rama, se crea el PR contra la rama principal con `Closes #N`, el issue pasa
   a *In Review* y recibe el comentario de avance.
4. **Given** el revisor, **When** se inspecciona su configuración, **Then** solo puede leer
   archivos y consultar el historial y el diff; no puede editar, escribir ni ejecutar otros
   comandos.
5. **Given** el comando corre en una rama que no sigue el patrón `NNN-slug` o sin issue
   identificable, **When** se invoca, **Then** se detiene y explica qué falta.

---

### User Story 3 - Cierre automático al fusionar (Priority: P3)

Como desarrollador, quiero que al fusionar el pull request el issue se cierre y pase a
*Done* sin intervención, y que ninguna regla del Project contradiga los estados que fija
el ciclo.

**Why this priority**: ya funciona gracias a la regla integrada del Project (verificado en
el issue #1); falta documentar la decisión y alinear la regla que podría contradecir el
paso a *In Review*.

**Independent Test**: fusionar el PR de este ticket y verificar en GitHub que el issue #2
queda cerrado y en *Done* sin movimientos manuales.

**Acceptance Scenarios**:

1. **Given** un PR con `Closes #N`, **When** se fusiona, **Then** el issue se cierra y el
   Project lo pasa a *Done* sin intervención.
2. **Given** la configuración de reglas del Project, **When** se crea un PR vinculado a un
   issue, **Then** ninguna regla mueve el issue a un estado distinto de *In Review*.
3. **Given** la documentación de decisiones, **When** se consulta, **Then** explica por qué
   se eligió la regla integrada frente a una automatización propia.

---

### User Story 4 - Flujo y definición de hecho documentados (Priority: P4)

Como desarrollador, quiero que la definición de hecho de un ticket y sus puntos de control
humanos estén documentados en las instrucciones del proyecto, y que los ajustes hechos en
cada punto de control queden registrados en el issue.

**Why this priority**: el flujo ya está resumido en las instrucciones del proyecto desde el
issue #1; falta completar la definición de hecho y el registro de ajustes.

**Independent Test**: leer las instrucciones del proyecto y confirmar la secuencia
completa y los tres puntos de control; revisar que el comentario de cierre de este ticket
incluye los ajustes de sus puntos de control.

**Acceptance Scenarios**:

1. **Given** las instrucciones del proyecto, **When** se leen, **Then** muestran la
   secuencia specify → (clarify) → plan → tasks → analyze → implement (→ converge) y los
   tres puntos de control humanos, con el merge como aprobación final.
2. **Given** un punto de control en el que se pidieron cambios, **When** se abre el PR,
   **Then** el comentario de avance del issue los registra en "qué se decidió".

---

### Edge Cases

- **Nada en *Todo***: el comando de inicio informa que no hay tickets disponibles y no
  cambia nada.
- **Siguiente ticket con dependencias abiertas**: se salta y se explica por qué; si ningún
  ticket es elegible, se informa sin cambiar nada.
- **Issue indicado ya en *In Progress* o cerrado**: el comando avisa y pide confirmación
  antes de continuar; con un issue cerrado, no continúa.
- **Árbol de trabajo con cambios sin commitear** al iniciar: el comando se detiene antes de
  crear la rama.
- **La rama ya existe**: el comando la reutiliza si corresponde al mismo issue o se detiene
  si no.
- **Ya existe un PR abierto para la rama**: el comando de PR no crea otro; actualiza el
  estado y el comentario.
- **Falla de red o del servidor MCP** a mitad de camino: el comando informa qué pasos se
  completaron y cuáles no; al reintentar, no duplica comentarios ni movimientos ya hechos.
- **Token sin permiso de projects**: el comando informa que no puede mover el ítem en
  lugar de fallar en silencio.

## Requirements *(mandatory)*

### Functional Requirements

**Inicio de ticket**

- **FR-001**: El proyecto MUST incluir un comando de inicio de ticket, versionado, que
  acepte opcionalmente un número de issue.
- **FR-002**: Sin número, el comando MUST elegir, entre los issues en *Todo*, el de menor
  número cuyas dependencias declaradas ("Depende de") estén cerradas, e informar la
  elección.
- **FR-003**: El comando MUST mover el issue a *In Progress* actualizando el ítem existente
  del Project (o agregándolo si falta), y comentar el inicio indicando la rama.
- **FR-004**: El comando MUST crear la rama `NNN-slug` y la carpeta de la spec, y lanzar la
  generación de la especificación con el título y el cuerpo del issue; la spec MUST
  enlazar el issue.
- **FR-005**: El comando MUST detenerse tras generar la spec y presentarla para revisión,
  sin encadenar plan, tareas ni implementación.
- **FR-006**: Las herramientas que el comando puede usar sin pedir permiso MUST limitarse a
  las de GitHub y a las mínimas para crear la rama y generar la spec.

**Revisión y pull request**

- **FR-007**: El proyecto MUST incluir un revisor independiente, versionado, que no
  comparta la conversación de la sesión que escribió el código y que solo pueda leer
  archivos y consultar el diff y el historial.
- **FR-008**: El revisor MUST comparar el diff de la rama contra su spec y reportar
  hallazgos clasificados como bloqueantes o no bloqueantes, con archivo y línea.
- **FR-009**: El proyecto MUST incluir un comando de apertura de PR, versionado, que
  invoque al revisor y se detenga sin publicar nada si hay bloqueantes.
- **FR-010**: Sin bloqueantes, el comando MUST publicar la rama, crear el PR contra la rama
  principal con `Closes #N`, mover el issue a *In Review* y comentar qué se especificó,
  qué se decidió (incluidos los ajustes de los puntos de control) y qué quedó pendiente.
- **FR-011**: El comando MUST deducir el número de issue de la rama y su spec, y detenerse
  si no puede.
- **FR-012**: Al reintentarse, los comandos MUST NOT duplicar PR, comentarios ni
  movimientos ya hechos.

**Cierre y reglas del Project**

- **FR-013**: El paso a *Done* al fusionar MUST ocurrir sin intervención, y la decisión
  sobre el mecanismo (regla integrada frente a automatización propia) MUST quedar
  documentada.
- **FR-014**: La regla del Project para PR vinculados MUST quedar configurada o desactivada
  de modo que no contradiga *In Review*, y su estado MUST quedar documentado.

**Flujo**

- **FR-015**: Las instrucciones del proyecto MUST documentar la definición de hecho
  completa y los tres puntos de control humanos, con el merge como aprobación final.
- **FR-016**: Este ticket MUST cerrarse usando el comando de apertura de PR que entrega.

### Key Entities

- **Ticket**: issue de GitHub con número, título, cuerpo, estado en el Project y sección
  "Depende de".
- **Rama de ticket**: `NNN-slug`, ligada a una carpeta `specs/NNN-slug/` cuya spec enlaza
  el issue.
- **Hallazgo de revisión**: severidad (bloqueante o no bloqueante), archivo, línea y
  descripción.
- **Comentario de avance**: comentario del issue en un hito del ciclo (inicio, PR) con lo
  especificado, lo decidido y lo pendiente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Desde el issue #3 en adelante, cero movimientos manuales de estado en el
  Project: todos los cambios a *In Progress*, *In Review* y *Done* los hacen los comandos o
  las reglas del Project.
- **SC-002**: El 100% de los PR abiertos con el comando incluyen `Closes #N` y dejan un
  comentario de avance en su issue.
- **SC-003**: En una prueba con un cambio que viola la spec, el comando de PR se detiene en
  el 100% de los casos sin publicar nada.
- **SC-004**: Iniciar un ticket hasta tener la spec lista para revisión toma un solo
  comando del desarrollador.
- **SC-005**: Un evaluador puede reconstruir el ciclo completo de este ticket (inicio,
  spec, PR, revisión, cierre) solo desde GitHub.

## Assumptions

- El arranque de este ticket fue manual (comentario de inicio hecho por el asistente vía el
  servidor MCP de GitHub), porque el comando de inicio es uno de sus entregables.
- La regla integrada "Item closed" del Project ya pasa los issues a *Done*; se verificó con
  el PR #15 (merge 19:29:55, *Done* 19:29:57). No se necesita automatización propia.
- La configuración de las reglas del Project solo se puede cambiar desde la interfaz web:
  el desarrollador la ajusta y el ticket documenta el resultado.
- En la prueba del issue #1, la regla "Pull request linked to issue" no movió el issue, y
  el PR no se agregó al Project; el comando de PR hace el paso a *In Review*.
- Spec Kit 1.2 no crea la rama sin su extensión de git: el comando de inicio la crea, junto
  con el puntero de la feature actual.
- La regla de selección por menor número con dependencias cerradas sustituye al orden de
  prioridad del documento de arranque; el desarrollador puede indicar un número para
  cambiar el orden.
- La revisión de cumplimiento de reglas de negocio queda fuera de alcance (issue #3); el
  comando de PR se diseña para incorporarla después.
