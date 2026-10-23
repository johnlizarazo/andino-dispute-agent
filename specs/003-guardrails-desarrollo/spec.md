# Feature Specification: Guardrails de desarrollo

**Feature Branch**: `003-guardrails-desarrollo`

**Created**: 2026-10-23

**Issue**: #3 (https://github.com/johnlizarazo/andino-dispute-agent/issues/3)

**Status**: Draft

**Input**: Issue #3 "Guardrails de desarrollo": garantías deterministas durante el desarrollo
para tests, spec-first, datos ficticios, formato y cumplimiento de las reglas de negocio.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Desarrollador**: trabaja con el asistente o escribe código y commits por su cuenta.
- **Asistente de programación**: sesión de Claude Code que edita archivos del repositorio.
- **Auditor de cumplimiento**: subagente de solo lectura que contrasta el código con la
  constitución.
- **Otro equipo del banco**: reutiliza las garantías empaquetadas (la prueba de
  instalación es del issue #14).

### User Story 1 - Ningún dato con forma real entra al repositorio (Priority: P1)

Como desarrollador de un repositorio público, quiero que cualquier escritura con algo que
tenga forma de número de tarjeta o documento de identidad real se bloquee, venga del
asistente o de un commit hecho por fuera, para que nunca se cometa la falta grave de "dato
que parezca real".

**Why this priority**: es falta grave según el enunciado, y el repositorio ya es público.

**Independent Test**: pedir al asistente que escriba un archivo con un número de tarjeta
válido por Luhn (generado en el momento) y verificar que se bloquea; repetir con montos y
con el formato ficticio y verificar que no se bloquean; hacer un commit por fuera del
asistente con un número válido y verificar que el control externo lo rechaza.

**Acceptance Scenarios**:

1. **Given** el asistente va a escribir un archivo con una secuencia de 13 a 19 dígitos que
   pasa Luhn, **When** intenta la escritura, **Then** se bloquea con un mensaje que explica
   qué se detectó, sin repetir el número completo.
2. **Given** el asistente va a escribir un número junto a "CC", "cédula" o "documento",
   **When** intenta la escritura, **Then** se bloquea.
3. **Given** el contenido tiene montos como `180000` o `1250000`, o el formato `CC-FIC-0001`,
   **When** el asistente escribe, **Then** la escritura se permite.
4. **Given** un desarrollador hace un commit por fuera del asistente con un número válido
   por Luhn, **When** el cambio llega a GitHub, **Then** un control automático falla y lo
   señala.
5. **Given** los tests del bloqueo, **When** se inspecciona el repositorio, **Then** no hay
   ningún literal con forma de tarjeta real: los números válidos se generan al correr.

---

### User Story 2 - No hay código sin especificación (Priority: P2)

Como desarrollador, quiero que el asistente no pueda escribir código de producción si el
ticket actual no tiene especificación, plan y tareas, para que spec-first sea una garantía
y no una costumbre.

**Why this priority**: es el principio IV de la constitución y una necesidad explícita del
enunciado; los tickets de código empiezan en el #4.

**Independent Test**: en una rama de ticket sin `plan.md`, pedir al asistente que cree un
archivo bajo `src/` y verificar el bloqueo; con los tres artefactos presentes, verificar
que se permite.

**Acceptance Scenarios**:

1. **Given** la rama actual no tiene `spec.md`, `plan.md` y `tasks.md` en `specs/<rama>/`,
   **When** el asistente intenta escribir bajo `src/`, **Then** se bloquea indicando qué
   artefacto falta.
2. **Given** los tres artefactos existen, **When** el asistente escribe bajo `src/`,
   **Then** se permite.
3. **Given** cualquier rama, **When** el asistente escribe fuera de `src/` (specs, docs,
   configuración), **Then** este control no interviene.
4. **Given** la rama es `main` o no sigue el patrón `NNN-slug`, **When** el asistente
   intenta escribir bajo `src/`, **Then** se bloquea.

---

### User Story 3 - El código queda formateado tras cada edición (Priority: P3)

Como desarrollador, quiero que cada archivo Python que edite el asistente quede formateado
y con las correcciones automáticas de estilo aplicadas, para que el código sea uniforme sin
depender de recordarlo.

**Why this priority**: necesidad explícita del enunciado; su valor crece cuando empieza el
código (#4).

**Independent Test**: pedir al asistente que escriba un archivo Python mal formateado y
verificar que, tras la edición, queda formateado.

**Acceptance Scenarios**:

1. **Given** el asistente edita un archivo `.py`, **When** termina la edición, **Then** el
   archivo queda formateado y con las correcciones automáticas aplicadas.
2. **Given** el asistente edita un archivo que no es `.py`, **When** termina, **Then** no se
   formatea.
3. **Given** el formateador encuentra un problema que no puede corregir solo, **When**
   termina, **Then** el asistente recibe el detalle para corregirlo, sin que la edición se
   pierda.

---

### User Story 4 - Revisión de cumplimiento antes del pull request (Priority: P4)

Como desarrollador, quiero que antes de abrir cada pull request un auditor independiente
verifique que las reglas de negocio y los principios de la constitución están implementados
como se especificaron, y que un incumplimiento detenga el pull request.

**Why this priority**: es la necesidad de "revisión de cumplimiento"; completa a
`/abrir-pr`, que hoy solo tiene revisión de código.

**Independent Test**: invocar la revisión de cumplimiento sobre una rama con un
incumplimiento sembrado y verificar que lo reporta como bloqueante; invocar `/abrir-pr` y
verificar que se detiene.

**Acceptance Scenarios**:

1. **Given** una rama de ticket, **When** se invoca la revisión de cumplimiento, **Then** el
   auditor revisa en un contexto aislado los principios I a III contra el código y los
   tests, ejecuta los tests deterministas y devuelve un veredicto con hallazgos ubicados.
2. **Given** el auditor, **When** se inspecciona su configuración, **Then** solo puede leer
   archivos y ejecutar los tests; no puede modificar nada.
3. **Given** un incumplimiento bloqueante, **When** se ejecuta `/abrir-pr`, **Then** el
   comando se detiene sin publicar nada.
4. **Given** una rama sin código de negocio todavía, **When** se audita, **Then** las reglas
   sin código aplicable se reportan como "no aplica", no como incumplimiento.

---

### User Story 5 - Convenciones por ruta (Priority: P5)

Como desarrollador, quiero que las convenciones de tests y de herramientas MCP se carguen
solo cuando se trabaja en los archivos donde aplican, para que todos los tests sigan las
mismas reglas en muchas carpetas sin inflar las instrucciones generales.

**Why this priority**: necesidad explícita ("tests junto al código, mismas convenciones en
muchas carpetas") y mínimo del ecosistema (2 rules con alcance por ruta).

**Independent Test**: abrir un archivo de test y comprobar que la convención de tests se
carga; abrir un archivo del servidor MCP y comprobar que se carga la convención de
herramientas.

**Acceptance Scenarios**:

1. **Given** el asistente trabaja en un archivo `test_*.py` bajo `src/` o en `tests/`,
   **When** lo lee o edita, **Then** recibe la convención de tests.
2. **Given** el asistente trabaja en el servidor MCP, **When** lo lee o edita, **Then**
   recibe la convención del contrato de errores y de las descripciones de herramientas.
3. **Given** el asistente trabaja en otros archivos, **When** los lee, **Then** esas
   convenciones no se cargan.

---

### User Story 6 - Garantías empaquetadas y consumidas por el propio repositorio (Priority: P6)

Como desarrollador, quiero que las garantías vivan en un paquete reutilizable que el propio
repositorio consume, para tener una sola fuente de verdad y dejar listo el paquete para otro
equipo.

**Why this priority**: necesidad de "piezas reutilizables por otro equipo" y mínimo del
plugin; la prueba de instalación externa es del #14.

**Independent Test**: clonar el repositorio, abrir una sesión del asistente y comprobar que
los controles de US1 a US3 están activos sin configuración manual.

**Acceptance Scenarios**:

1. **Given** un clon nuevo, **When** se abre una sesión y se aceptan los avisos de confianza
   del repositorio, **Then** los controles de datos, spec-first y formato están activos.
2. **Given** se modifica un control del paquete, **When** el desarrollador sigue el
   procedimiento documentado, **Then** la sesión usa la versión nueva.
3. **Given** el paquete, **When** se inspecciona, **Then** contiene al menos un subagente,
   una skill y un control reutilizables.

---

### Edge Cases

- **Número de tarjeta partido** con espacios o guiones (`NNNN NNNN NNNN NNNN`): se detecta igual.
- **Secuencias largas que no pasan Luhn** (identificadores, marcas de tiempo, hashes): no se
  bloquean.
- **Documentación que habla del formato** ("13 a 19 dígitos", `CC-FIC-NNNN`): no se bloquea.
- **Edición parcial**: el control revisa el texto nuevo que se escribe, no todo el archivo.
- **El control de datos falla internamente** (error inesperado): falla cerrado y bloquea con
  un mensaje claro, para no dejar pasar un dato real por un error.
- **Formateador no instalado**: el asistente recibe un aviso; la edición no se bloquea.
- **Rama de ticket recién creada** sin spec: escribir en `specs/` se permite (es como nace la
  spec); escribir en `src/` no.
- **Auditor sin acceso a la API**: solo corre los tests deterministas; nunca los `e2e`.

## Requirements *(mandatory)*

### Functional Requirements

**Datos con forma real**

- **FR-001**: Toda escritura o edición del asistente MUST bloquearse si el texto nuevo
  contiene una secuencia de 13 a 19 dígitos (admitiendo espacios o guiones entre grupos)
  que pasa la validación de Luhn.
- **FR-002**: MUST bloquearse también un número de 6 a 10 dígitos precedido por una palabra
  de documento ("CC", "C.C.", "cédula", "documento", "NIT", "pasaporte"), salvo el formato
  ficticio `CC-FIC-NNNN`.
- **FR-003**: Montos de hasta 12 dígitos sin palabra de documento y secuencias que no pasan
  Luhn MUST NOT bloquearse.
- **FR-004**: El mensaje de bloqueo MUST indicar el tipo de dato detectado y su ubicación
  aproximada sin repetir el valor completo.
- **FR-005**: Ante un error interno, el control MUST fallar cerrado (bloquear).
- **FR-006**: Los tests del control MUST generar en tiempo de ejecución los números válidos
  por Luhn; el repositorio MUST NOT contener literales con forma de tarjeta real.
- **FR-007**: El mismo chequeo MUST ejecutarse automáticamente sobre los cambios que llegan
  a GitHub, para cubrir commits hechos fuera del asistente.

**Spec-first**

- **FR-008**: Toda escritura del asistente bajo `src/` MUST bloquearse si la rama actual no
  sigue `NNN-slug` o si falta `spec.md`, `plan.md` o `tasks.md` en `specs/<rama>/`,
  indicando qué falta.
- **FR-009**: El control de spec-first MUST NOT intervenir en escrituras fuera de `src/`.

**Formato**

- **FR-010**: Tras cada escritura o edición del asistente sobre un archivo `.py`, el archivo
  MUST formatearse y recibir las correcciones automáticas de estilo.
- **FR-011**: Los problemas que no se corrigen solos MUST devolverse al asistente sin
  bloquear ni revertir la edición.

**Cumplimiento**

- **FR-012**: El proyecto MUST incluir un auditor de cumplimiento con contexto aislado que
  solo pueda leer archivos y ejecutar los tests deterministas.
- **FR-013**: El proyecto MUST incluir una revisión de cumplimiento invocable que ejecute al
  auditor de forma aislada, acepte opcionalmente una ruta o módulo y devuelva un veredicto
  con hallazgos bloqueantes y no bloqueantes ubicados.
- **FR-014**: El auditor MUST verificar los principios I a III de la constitución y reportar
  como "no aplica" las reglas sin código aplicable.
- **FR-015**: `/abrir-pr` MUST invocar la revisión de cumplimiento después de la revisión de
  código y detenerse sin publicar si hay bloqueantes.

**Convenciones por ruta**

- **FR-016**: MUST existir una convención de tests que aplique solo a `src/**/test_*.py` y
  `tests/**/*.py`.
- **FR-017**: MUST existir una convención de herramientas MCP que aplique solo a
  `src/core_bancario_mcp/**/*.py`, con el contrato de errores y las reglas de descripción.

**Empaquetado**

- **FR-018**: Los controles de datos, spec-first y formato, el auditor y la revisión de
  cumplimiento MUST vivir en un paquete reutilizable dentro del repositorio, publicado en un
  catálogo del propio repositorio.
- **FR-019**: El repositorio MUST consumir ese paquete por configuración compartida, sin
  pasos manuales al clonar más allá de aceptar la confianza del repositorio.
- **FR-020**: MUST quedar documentado cómo hacer que la sesión use una versión nueva del
  paquete tras modificarlo.

### Key Entities

- **Hallazgo de datos**: tipo (tarjeta o documento), archivo y ubicación aproximada; nunca
  el valor completo.
- **Artefactos del ticket**: `spec.md`, `plan.md`, `tasks.md` en `specs/<rama>/`.
- **Veredicto de cumplimiento**: aprobado o bloqueado, con hallazgos por principio y regla.
- **Paquete de garantías**: controles, auditor, revisión de cumplimiento y su catálogo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de un conjunto de al menos 20 números de tarjeta válidos por Luhn,
  generados al correr las pruebas (con y sin separadores), se bloquea.
- **SC-002**: Cero falsos positivos sobre un conjunto de al menos 20 casos legítimos
  (montos del enunciado, `CC-FIC-NNNN`, secuencias que no pasan Luhn, documentación del
  formato).
- **SC-003**: El 100% de los intentos de escribir bajo `src/` sin los tres artefactos se
  bloquea, y el 100% con los tres presentes se permite.
- **SC-004**: El 100% de los archivos Python editados por el asistente quedan formateados
  sin intervención.
- **SC-005**: Un incumplimiento sembrado de los principios I a III detiene `/abrir-pr` en el
  100% de los casos probados.
- **SC-006**: Un clon nuevo tiene los controles activos con cero pasos de configuración
  aparte de aceptar la confianza del repositorio.

## Assumptions

- El catálogo y el paquete se crean en este ticket porque los controles no se cargan sin
  ellos; la prueba de instalación en otro repositorio es del issue #14.
- Para los commits hechos fuera del asistente se prefiere un control automático en GitHub
  sobre un hook de pre-commit local, porque este último exige instalación manual por cada
  desarrollador; el plan confirma el mecanismo.
- Los controles de datos y spec-first aplican a las herramientas de escritura y edición del
  asistente; escrituras por comandos de consola quedan cubiertas por el control en GitHub.
- La rama de este ticket no agrega código bajo `src/`, así que el control de spec-first no
  interfiere con su propia implementación.
- El auditor trabaja sin acceso a la API: solo ejecuta los tests deterministas.
- En esta rama también se marcan las tareas T016 a T020 del issue #2, como se acordó en su
  análisis; no es parte del alcance funcional de este ticket.
- Fuera de alcance: prueba de instalación en otro repositorio y documentación para otros
  equipos (issue #14).
