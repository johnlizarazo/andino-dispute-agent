# Feature Specification: Plugin, marketplace y DECISIONES.md

**Feature Branch**: `014-plugin-marketplace-decisiones`

**Created**: 2026-10-26

**Issue**: #14 (https://github.com/johnlizarazo/andino-dispute-agent/issues/14)

**Status**: Approved

**Input**: Issue #14: que otro equipo del banco pueda instalar las piezas reutilizables desde
el marketplace del repositorio (plugin `andino-guardrails`, con al menos un subagente, una
skill y un hook, probado en un repositorio vacío); el documento `DECISIONES.md` (máximo dos
páginas) con el mecanismo elegido por necesidad y la alternativa descartada; un script
versionado que arma el `.zip` de entrega (con `.git`, sin `.venv`, `.env*`, cachés ni
dependencias, de menos de 50 MB y sin credenciales); y que los evaluadores accedan al
repositorio y al Project sin pedir acceso.

## User Scenarios & Testing *(mandatory)*

Actores:

- **Otro equipo del banco**: quiere los guardrails en su propio repositorio sin copiar
  archivos.
- **Evaluador**: revisa el entregable (el `.zip`, el repositorio, el Project y
  `DECISIONES.md`) y defiende o cuestiona las decisiones.
- **Desarrollador**: arma la entrega y mantiene el plugin.

### User Story 1 - Instalar los guardrails en otro repositorio (Priority: P1)

Como otro equipo del banco, quiero agregar el marketplace del repositorio e instalar el
plugin `andino-guardrails` con dos comandos, para tener los mismos guardrails sin copiar
archivos.

**Why this priority**: es la necesidad del issue (reutilización entre equipos) y su
criterio de prueba principal.

**Independent Test**: en un repositorio vacío, ejecutar los dos comandos de instalación y
comprobar que el plugin queda instalado y que sus piezas responden.

**Acceptance Scenarios**:

1. **Given** el plugin publicado, **When** se revisa su contenido, **Then** empaqueta al
   menos un subagente (`auditor-cumplimiento`), una skill (`revisar-cumplimiento`) y un hook
   (`bloquear_pii`, `exigir_spec` y `formatear`).
2. **Given** un repositorio vacío con Claude Code, **When** se ejecuta
   `/plugin marketplace add johnlizarazo/andino-dispute-agent` y luego
   `/plugin install andino-guardrails@banco-andino`, **Then** el plugin queda instalado y
   habilitado.
3. **Given** el plugin instalado en ese repositorio, **When** Claude Code intenta escribir
   un archivo con un número con forma de tarjeta real, **Then** el hook lo bloquea.
4. **Given** el plugin instalado, **When** se lista lo que aporta, **Then** aparecen el
   subagente y la skill del plugin.
5. **Given** la documentación del plugin, **When** otro equipo la lee, **Then** encuentra
   los requisitos (`uv`, `ruff` opcional), los dos comandos de instalación, la alternativa
   por `settings.json` y qué hace cada pieza, incluido que `exigir_spec` exige spec, plan y
   tareas para escribir bajo `src/`.

---

### User Story 2 - Entender las decisiones en dos páginas (Priority: P1)

Como evaluador, quiero un `DECISIONES.md` breve que diga, por cada necesidad, qué mecanismo
del ecosistema de Claude Code se eligió, dónde está y qué alternativa se descartó, para
evaluar las decisiones sin recorrer todos los tickets.

**Why this priority**: es un entregable explícito y lo exige el principio VII de la
constitución ("su justificación queda en `DECISIONES.md`").

**Independent Test**: leer `DECISIONES.md` y comprobar que cada pieza del ecosistema del
repositorio aparece con su necesidad, mecanismo, ubicación y alternativa descartada, en dos
páginas como máximo.

**Acceptance Scenarios**:

1. **Given** las piezas del ecosistema del repositorio (memoria, reglas, skills, comando,
   subagentes, hooks, permisos, servidores MCP, plugin, marketplace y CI), **When** se lee
   `DECISIONES.md`, **Then** cada una aparece con la necesidad que resuelve, el mecanismo
   elegido, dónde está y la alternativa descartada con su motivo.
2. **Given** `DECISIONES.md`, **When** se mide, **Then** no supera dos páginas.
3. **Given** las decisiones ya registradas en los `research.md` de cada ticket, **When** se
   comparan con `DECISIONES.md`, **Then** no se contradicen, y cada entrada enlaza al ticket
   o `research.md` donde se decidió.
4. **Given** el agente construido (no solo el ecosistema de Claude Code), **When** se lee
   `DECISIONES.md`, **Then** también resume en qué nivel queda cada regla de negocio:
   imposible por diseño, hook u orientada por instrucción y verificada por test.

---

### User Story 3 - Armar la entrega con un script (Priority: P2)

Como desarrollador, quiero un script versionado que arme el `.zip` de entrega con el
historial de git y sin archivos locales, dependencias, cachés ni secretos, y que verifique
el tamaño y la ausencia de credenciales, para entregar sin errores manuales.

**Why this priority**: es un entregable del issue; depende de que lo demás esté listo.

**Independent Test**: correr el script en Windows y en Linux/macOS y comprobar el
contenido, el tamaño y el resultado de la verificación.

**Acceptance Scenarios**:

1. **Given** el repositorio, **When** se corre el script, **Then** produce un `.zip` que
   incluye `.git` y los archivos del proyecto.
2. **Given** el `.zip`, **When** se inspecciona, **Then** no contiene `.venv`, archivos
   `.env*` (salvo `.env.example`), cachés (`__pycache__`, `.pytest_cache`, `.ruff_cache`),
   dependencias ni archivos generados localmente (`.chainlit/`, `.files/`,
   `.claude/settings.local.json`, `CLAUDE.local.md`).
3. **Given** el `.zip`, **When** el script lo verifica, **Then** falla si pesa 50 MB o más e
   informa el tamaño.
4. **Given** el contenido del `.zip`, **When** el script lo revisa, **Then** falla si
   encuentra algo con forma de credencial (tokens de GitHub, claves de API de Anthropic u
   otras claves privadas) y dice en qué archivo, sin mostrar el valor.
5. **Given** que el script falla, **When** termina, **Then** no deja un `.zip` que parezca
   válido.

---

### User Story 4 - Acceso sin pedir permiso (Priority: P2)

Como evaluador, quiero abrir el repositorio y el Project sin pedir acceso, para revisar el
avance del proyecto solo con GitHub (principio VII).

**Why this priority**: sin acceso no se puede evaluar; es una configuración de GitHub que
se verifica una vez.

**Independent Test**: abrir el repositorio y el Project desde una sesión sin iniciar en
GitHub.

**Acceptance Scenarios**:

1. **Given** una sesión sin iniciar en GitHub, **When** se abre el repositorio, **Then** se
   ve su código, sus issues y sus pull requests.
2. **Given** la misma sesión, **When** se abre el enlace del Project del README, **Then** se
   ven los ítems y su estado.

---

### Edge Cases

- El plugin se instala en un repositorio que no sigue el flujo spec-first: `exigir_spec`
  bloquea las escrituras bajo `src/`. La documentación lo advierte y explica cómo
  deshabilitar el plugin o ese hook.
- El equipo no tiene `uv` instalado: los hooks no pueden correr; la documentación lo pone
  como requisito.
- El equipo no tiene `ruff` en su proyecto: `formatear` avisa sin bloquear.
- El agente auditor del plugin está pensado para la constitución de este proyecto: en otro
  repositorio audita contra la constitución que encuentre, o informa que no la hay.
- El `.zip` incluye el video de `docs/` y el historial de git, que también lo contiene: el
  script mide el tamaño real y avisa con margen si se acerca al límite.
- Hay archivos sin versionar en la carpeta (por ejemplo, `.claude/launch.json` excluido
  localmente): no entran al `.zip`.
- Un archivo versionado contiene un valor parecido a una credencial en un test o en la
  documentación (por ejemplo, un prefijo de ejemplo): el script no da falsos positivos con
  los ejemplos documentados del propio repositorio y, ante una coincidencia real, falla.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El plugin `andino-guardrails` DEBE empaquetar al menos un subagente, una
  skill y un hook, declarados de forma que Claude Code los cargue al instalarlo.
- **FR-002**: El marketplace `banco-andino` DEBE poder agregarse con
  `/plugin marketplace add johnlizarazo/andino-dispute-agent`, y el plugin DEBE instalarse
  con `/plugin install andino-guardrails@banco-andino` en un repositorio vacío.
- **FR-003**: La instalación en un repositorio vacío DEBE quedar verificada y su resultado
  registrado: comandos, que el plugin quedó habilitado, que el hook de datos bloquea y que
  el subagente y la skill aparecen.
- **FR-004**: La documentación del plugin DEBE explicar requisitos, instalación por comandos
  y por `settings.json`, qué hace cada pieza y cómo deshabilitar el plugin o un hook.
- **FR-005**: `DECISIONES.md` DEBE existir en la raíz, con máximo dos páginas, y listar por
  necesidad el mecanismo elegido, su ubicación y la alternativa descartada con su motivo.
- **FR-006**: `DECISIONES.md` DEBE cubrir todas las piezas del ecosistema del repositorio y
  el nivel de garantía de cada regla de negocio, y enlazar al ticket o `research.md` donde
  se tomó cada decisión, sin contradecirlos.
- **FR-007**: DEBE existir un script versionado que arme el `.zip` de entrega con los
  archivos versionados del proyecto y el directorio `.git`.
- **FR-008**: El script DEBE excluir `.venv`, `.env*` (salvo `.env.example`), cachés,
  dependencias y archivos locales o generados.
- **FR-009**: El script DEBE fallar si el `.zip` pesa 50 MB o más, informando el tamaño.
- **FR-010**: El script DEBE fallar si encuentra contenido con forma de credencial,
  indicando el archivo sin mostrar el valor.
- **FR-011**: El script DEBE funcionar en Windows y en Linux/macOS, y su uso DEBE quedar en
  el README.
- **FR-012**: El repositorio y el Project DEBEN ser visibles sin iniciar sesión, y esa
  verificación DEBE quedar registrada.

### Key Entities

- **Plugin**: paquete instalable con subagente, skill y hooks, publicado en un marketplace.
- **Marketplace**: catálogo de plugins que otro repositorio agrega por su nombre.
- **Decisión**: necesidad, mecanismo elegido, ubicación, alternativa descartada y origen
  (ticket o `research.md`).
- **Entrega**: el `.zip` con el proyecto versionado y su historial.

## Garantías (Principio II)

Esta funcionalidad no agrega reglas de negocio. La verificación de la entrega (tamaño y
credenciales) es determinista: la hace el script y falla cerrado. La instalación del plugin
y la visibilidad en GitHub se verifican una vez de forma manual y se registran, porque
dependen de Claude Code y de la configuración de GitHub.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En un repositorio vacío, el plugin queda instalado con 2 comandos y su hook de
  datos bloquea los 2 casos de prueba (una tarjeta y un documento con forma real).
- **SC-002**: `DECISIONES.md` cubre el 100 % de las piezas del ecosistema del repositorio y
  ocupa como máximo 2 páginas.
- **SC-003**: El `.zip` pesa menos de 50 MB, contiene el historial de git y 0 archivos
  excluidos o con forma de credencial.
- **SC-004**: Un evaluador sin sesión en GitHub abre el repositorio y el Project al primer
  intento.
- **SC-005**: El script arma y verifica la entrega en menos de 1 minuto.

## Assumptions

- El plugin ya existe desde el #3 con las piezas que pide el issue; este ticket verifica la
  instalación desde otro repositorio y completa su documentación, sin cambiar lo que hacen
  los hooks.
- "Dos páginas" equivale a unas 900 palabras en formato Markdown con tablas.
- Las decisiones ya están razonadas en los `research.md` de cada ticket; `DECISIONES.md` las
  resume, no las reabre.
- El `.zip` se arma desde los archivos versionados (más `.git`), así que lo que no está en
  git no se entrega.
- La visibilidad del repositorio y del Project la cambia el desarrollador en GitHub; el
  ticket la verifica y la registra.
- Depende de #2 y #3, ya cerrados.
