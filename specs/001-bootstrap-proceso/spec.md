# Feature Specification: Bootstrap del proceso

**Feature Branch**: `001-bootstrap-proceso`

**Created**: 2026-10-21

**Status**: Draft

**Issue**: #1 (https://github.com/johnlizarazo/andino-dispute-agent/issues/1)

**Input**: Issue #1 "Bootstrap del proceso": base sobre la que se construye todo (Spec Kit,
constitución, convenciones mínimas, protección de secretos y conexión con GitHub).

## User Scenarios & Testing *(mandatory)*

Actores:

- **Desarrollador del equipo**: clona el repositorio y trabaja con el asistente de
  programación (Claude Code).
- **Asistente de programación**: sesión de Claude Code que lee convenciones, ejecuta
  comandos de Spec Kit y opera sobre GitHub.
- **Evaluador**: revisa el repositorio público y el Project para reconstruir el proceso.

### User Story 1 - Los secretos quedan fuera de alcance (Priority: P1)

Como desarrollador de un repositorio público, quiero que los archivos de secretos y
variables de entorno no puedan versionarse ni ser leídos o modificados por el asistente,
para que ninguna credencial se filtre al repositorio, a la entrega ni a una conversación.

**Why this priority**: el repositorio ya es público; una credencial expuesta es falta grave
y no tiene vuelta atrás. Es la protección que debe existir antes que cualquier otra pieza.

**Independent Test**: con un archivo `.env` de prueba (valores ficticios) en la raíz, pedir
al asistente que lo lea, lo busque, lo muestre por consola y lo edite; todas las vías se
bloquean, y el archivo no aparece como candidato a commit.

**Acceptance Scenarios**:

1. **Given** existe un archivo `.env` en la raíz, **When** el asistente intenta leerlo con
   sus herramientas de lectura o búsqueda, **Then** la operación se niega.
2. **Given** existe un archivo `.env`, **When** el asistente intenta mostrarlo o modificarlo
   con comandos de consola comunes, **Then** la operación se niega.
3. **Given** existen `.env` y `.env.local`, **When** el desarrollador revisa el estado de
   git, **Then** ninguno aparece como archivo a versionar, pero `.env.example` sí.
4. **Given** el repositorio, **When** se busca cualquier valor de credencial en archivos
   versionados, **Then** no se encuentra ninguno; solo nombres de variables.

---

### User Story 2 - Convenciones del equipo al clonar (Priority: P2)

Como desarrollador que clona el repositorio, quiero recibir las convenciones del equipo y
poder usar los comandos de Spec Kit sin configurar nada a mano, en cualquier sistema
operativo, y que mis preferencias personales no afecten a nadie más.

**Why this priority**: es la necesidad de "convenciones sin configurar nada" y
"preferencias personales aisladas"; sin ella cada sesión del asistente arranca sin los
principios del proyecto.

**Independent Test**: clonar en un directorio limpio, abrir una sesión del asistente y
verificar que conoce los principios de la constitución y que los comandos de Spec Kit
funcionan; crear archivos de preferencias personales y verificar que git los ignora.

**Acceptance Scenarios**:

1. **Given** un clon nuevo, **When** se abre una sesión del asistente, **Then** la
   constitución forma parte de su contexto sin que el desarrollador la cargue.
2. **Given** un clon nuevo en Windows, Linux o macOS, **When** se ejecuta un comando de
   Spec Kit que imprime resultados con acentos, **Then** termina sin errores de
   codificación y sin configuración manual.
3. **Given** un desarrollador crea su archivo de memoria personal y su configuración local
   del asistente, **When** revisa el estado de git, **Then** ambos están ignorados.
4. **Given** las instrucciones generales del proyecto, **When** se comparan con la
   constitución, **Then** no duplican su contenido: la referencian.

---

### User Story 3 - El asistente opera el Project de GitHub (Priority: P3)

Como desarrollador, quiero que el asistente pueda leer y actualizar el backlog en el
GitHub Project usando una conexión configurada en el repositorio sin credenciales, para que
los tickets posteriores puedan automatizar su ciclo.

**Why this priority**: es prerrequisito del issue #2; si el asistente no puede escribir en
el Project, la automatización del ciclo de tickets no es posible.

**Independent Test**: con el token definido como variable de entorno, pedir al asistente
que mueva un ítem del Project de un estado a otro y verificarlo en GitHub.

**Acceptance Scenarios**:

1. **Given** el token está definido en el entorno del desarrollador, **When** se abre una
   sesión, **Then** el asistente dispone de las herramientas de issues, pull requests y
   projects de GitHub.
2. **Given** la conexión activa, **When** el asistente mueve el issue #1 a otro estado,
   **Then** el cambio se refleja en el Project.
3. **Given** el archivo de configuración de la conexión, **When** se inspecciona, **Then**
   solo contiene referencias a variables de entorno, ningún valor de token.
4. **Given** un desarrollador nuevo, **When** consulta la documentación del repositorio,
   **Then** encuentra qué tipo de token crear y con qué permisos.

---

### User Story 4 - Estructura base del proyecto (Priority: P4)

Como desarrollador, quiero que el proyecto declare su propósito y los dos componentes que
se construirán (el agente y el servidor que simula el core bancario), y que sus
dependencias se instalen desde cero sin errores, para que los tickets siguientes partan de
una base estable.

**Why this priority**: los tickets del servidor y del agente dependen de que existan sus
paquetes, pero ninguno de ellos empieza en este ticket.

**Independent Test**: borrar el entorno local, reinstalar dependencias desde cero e
importar ambos paquetes.

**Acceptance Scenarios**:

1. **Given** un clon sin entorno local, **When** se instalan las dependencias, **Then** la
   instalación termina sin errores con la versión de Python del proyecto.
2. **Given** el entorno instalado, **When** se importan el paquete del agente y el del
   servidor, **Then** ambos importan sin errores.
3. **Given** la metadata del proyecto, **When** se consulta, **Then** tiene una
   descripción real, no la de ejemplo.

---

### Edge Cases

- **Variantes de nombre**: `.env.local`, `.env.production` o `config/.env` también quedan
  ignorados y protegidos; `.env.example` no.
- **Rutas alternativas por consola**: los comandos de consola permiten muchas formas de
  leer un archivo; la protección cubre las formas comunes (mostrar, copiar, buscar,
  editar) y la limitación residual queda documentada.
- **Token ausente**: si la variable del token no está definida, la conexión con GitHub
  falla de forma visible y no se pide ni se guarda el token en ningún archivo.
- **Token sin permiso de projects**: el asistente puede leer issues pero no mover ítems;
  la documentación indica cómo detectar y corregir el permiso.
- **Ítem ya presente en el Project**: el Project agrega issues automáticamente; la
  verificación no debe asumir que el ítem falta.
- **Desarrollador en Linux o macOS**: los comandos de Spec Kit y la instalación funcionan
  igual que en Windows.

## Requirements *(mandatory)*

### Functional Requirements

**Protección de secretos**

- **FR-001**: El repositorio MUST excluir del control de versiones todo archivo cuyo nombre
  empiece por `.env`, excepto `.env.example`.
- **FR-002**: La configuración compartida del asistente MUST negar la lectura y la edición
  de archivos `.env*` tanto por sus herramientas de archivos como por comandos de consola
  comunes.
- **FR-003**: El repositorio MUST incluir `.env.example` con los nombres de las variables
  necesarias y sin ningún valor.
- **FR-004**: Ningún archivo versionado MUST contener valores de credenciales.

**Convenciones compartidas y personales**

- **FR-005**: El repositorio MUST incluir instrucciones generales del proyecto para el
  asistente, breves, que importen la constitución en lugar de copiarla.
- **FR-006**: El repositorio MUST excluir del control de versiones el archivo de memoria
  personal del asistente y su configuración local.
- **FR-007**: La configuración compartida del asistente MUST fijar el modo UTF-8 del
  intérprete para que los comandos de Spec Kit funcionen en cualquier sistema operativo
  sin configuración manual.
- **FR-008**: Spec Kit MUST estar inicializado y versionado (su carpeta de soporte y sus
  skills), con scripts multiplataforma.
- **FR-009**: La constitución MUST estar versionada e incluir las cinco reglas de negocio,
  el uso exclusivo de datos ficticios, el criterio de hooks frente a instrucciones,
  spec-first y la estrategia de tests en dos niveles.

**Conexión con GitHub**

- **FR-010**: El repositorio MUST declarar la conexión con el servidor MCP de GitHub a
  nivel de proyecto, con los conjuntos de herramientas de contexto, repositorios, issues,
  pull requests y projects habilitados.
- **FR-011**: La declaración de la conexión MUST referenciar el token solo por variable de
  entorno.
- **FR-012**: La documentación MUST indicar el tipo de token requerido y sus permisos (token
  clásico con permiso de projects, para Projects de una cuenta personal) y dónde guardarlo.
- **FR-013**: Se MUST verificar, y dejar evidencia en el issue, que el asistente mueve un
  ítem del Project mediante la conexión.

**Estructura del proyecto**

- **FR-014**: La metadata del proyecto MUST tener una descripción real.
- **FR-015**: El proyecto MUST declarar dos paquetes, uno para el agente y otro para el
  servidor que simula el core bancario, que reemplazan al paquete de ejemplo.
- **FR-016**: La instalación de dependencias desde cero MUST terminar sin errores con la
  versión de Python del proyecto.

**Proceso**

- **FR-017**: El ticket MUST tener su especificación, plan y tareas versionados en su
  carpeta de `specs/`, y el pull request que lo cierre MUST referenciar el issue #1.

### Key Entities

- **Configuración compartida del asistente**: permisos y entorno que aplican a todo el
  equipo; versionada.
- **Configuración personal**: memoria y ajustes propios de un desarrollador; nunca
  versionada.
- **Conexión MCP de GitHub**: declaración del servidor, sus conjuntos de herramientas y la
  referencia al token.
- **Token de GitHub**: credencial personal del desarrollador; vive solo en su entorno.
- **Constitución**: principios no negociables del proyecto; fuente única de verdad.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los intentos del asistente de leer, buscar, mostrar o editar un
  archivo `.env` por las vías probadas (herramientas de archivos y al menos cuatro comandos
  de consola comunes) son negados.
- **SC-002**: Cero valores de credenciales en el historial completo del repositorio.
- **SC-003**: Un desarrollador que clona necesita cero pasos de configuración del asistente
  más allá de definir sus variables de entorno.
- **SC-004**: Los comandos de Spec Kit se ejecutan sin errores de codificación en el primer
  intento en un clon nuevo.
- **SC-005**: La instalación de dependencias desde cero termina en menos de 2 minutos con
  conexión estándar.
- **SC-006**: El asistente mueve un ítem del Project en el primer intento, y el cambio es
  visible en GitHub.
- **SC-007**: Un evaluador puede reconstruir el inicio del proyecto (issue, comentarios,
  pull request, cambios de estado) solo desde GitHub.

## Assumptions

- Ya están cumplidos y solo se verifican: repositorio público con rama principal `main`,
  Spec Kit inicializado y constitución 1.0.0 aprobada.
- El issue #1 se movió a *In Progress* manualmente: es el único movimiento manual del
  proyecto, porque la automatización nace en el issue #2.
- El pull request de este ticket se crea manualmente con `Closes #1`; el comando propio
  para abrir pull requests nace en el issue #2.
- El token se guarda como variable de entorno del usuario del sistema operativo; la
  protección es de nivel desarrollo, no un gestor de secretos.
- La protección contra lectura por consola es de mejor esfuerzo para comandos comunes; la
  garantía fuerte es que los secretos nunca estén versionados.
- Los paquetes del agente y del servidor se crean vacíos; su contenido pertenece a issues
  posteriores.
- Fuera de alcance: automatización del ciclo de tickets (#2), hooks de calidad (#3) y el
  servidor `core-bancario` (#4 en adelante).
