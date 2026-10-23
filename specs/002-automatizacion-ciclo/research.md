# Research: Automatización del ciclo en GitHub

Fase 0 del plan. Fuentes: documentación de Claude Code (`code.claude.com/docs/en/skills`,
`sub-agents`, `permissions`), las herramientas del servidor MCP de GitHub usadas en el
issue #1 y lo observado en el Project durante el cierre del PR #15.

## R1. Qué mecanismo implementa cada pieza

- **Decision**:

  | Pieza | Mecanismo | Ubicación |
  |---|---|---|
  | Inicio de ticket | Skill `siguiente-ticket` | `.claude/skills/siguiente-ticket/SKILL.md` |
  | Revisión independiente | Subagente `revisor-codigo` | `.claude/agents/revisor-codigo.md` |
  | Apertura de PR | Comando `/abrir-pr` | `.claude/commands/abrir-pr.md` |
  | Paso a *Done* | Regla integrada "Item closed" del Project | GitHub (sin archivo) |

- **Rationale**:
  - **Inicio como skill:** necesita argumento opcional (`argument-hint`), pre-aprobación de
    herramientas (`allowed-tools`) y que su resultado (la spec) quede en la conversación
    para el punto de control. Por eso **no** usa `context: fork`.
  - **Revisor como subagente:** arranca con contexto aislado; no ve la conversación ni los
    archivos que la sesión ya leyó. Eso es lo que hace "independiente" a la revisión.
  - **Apertura de PR como comando de `.claude/commands/`:** es la forma documentada de un
    comando versionado (sigue soportada, fusionada con skills). Cumple el mínimo de
    "comando propio" sin ambigüedad frente al mínimo de skills.
- **Alternatives considered**:
  - Todo como skills: válido, pero en la defensa se confunde con el mínimo de 2 skills.
  - Revisión en la misma sesión: no es independiente.
  - Un hook que abra el PR: los hooks reaccionan a eventos; abrir un PR es una decisión
    del desarrollador.

## R2. Semántica de `allowed-tools` y cómo "limitar al MCP de GitHub"

- **Decision**: `allowed-tools` de `siguiente-ticket` pre-aprueba solo:
  - Las herramientas del MCP de GitHub que usa, con nombre explícito:
    `mcp__github__projects_list`, `mcp__github__projects_write`,
    `mcp__github__issue_read`, `mcp__github__add_issue_comment`.
  - `Bash(git status *)` y `Bash(git checkout -b *)`.
- **Rationale**:
  - `allowed-tools` **pre-aprueba**: las herramientas listadas no piden permiso durante el
    turno que invoca la skill. **No restringe**: las demás siguen disponibles y las
    gobiernan los permisos normales. "Limitado al MCP de GitHub" significa que solo eso
    corre sin preguntar; lo demás, como la escritura de la spec por `speckit-specify`, sí
    pide permiso.
  - Se usan nombres explícitos y no `mcp__github__*`: la documentación no confirma
    comodines dentro de `allowed-tools`, y los nombres explícitos documentan mejor qué hace
    la skill.
  - Crear la rama necesita Git, que está fuera del MCP: es lo mínimo que exige FR-006.
- **Alternatives considered**:
  - `disallowed-tools` para restringir de verdad: bloquearía la escritura de la spec, que
    ocurre en el mismo turno.
  - Comodín `mcp__github__*`: no verificado en `allowed-tools`.

## R3. Revisor de solo lectura con Git acotado

- **Decision**: `revisor-codigo` con:
  - `tools: Read, Grep, Glob, Bash`.
  - `permissionMode: dontAsk`: niega cualquier herramienta que no esté pre-aprobada.
  - Reglas `permissions.allow` en `.claude/settings.json` para `Bash(git diff *)`,
    `Bash(git log *)` y `Bash(git show *)`.
- **Rationale**:
  - El campo `tools` solo acepta nombres de herramientas, no patrones como
    `Bash(git diff *)`. Restringir Bash requiere otra capa.
  - Con `dontAsk`, todo comando que no esté en `allow` se niega sin preguntar, así que el
    revisor no puede ejecutar nada más.
  - Las tres reglas `allow` son de solo lectura e inofensivas para el resto del equipo.
  - Es declarativo: no agrega código.
- **Riesgo y verificación**: la documentación no detalla cómo trata `dontAsk` a Read, Grep
  y Glob. La verificación (quickstart §3) pide al revisor un comando no permitido
  (`git status`) y uno permitido (`git diff`).
- **Fallback documentado**: si `dontAsk` no se comporta así, se usa un hook `PreToolUse`
  en el frontmatter del subagente que solo deja pasar `git diff`, `git log` y `git show`.
- **Alternatives considered**:
  - Sin Bash, con el diff pegado en el mensaje de delegación: es más simple, pero el
    revisor no puede inspeccionar el historial por su cuenta, y el issue pide `git diff` y
    `git log`.
  - `disallowedTools: Bash(...)`: quita Bash completo.

## R4. Invocación entre piezas

- **Decision**:
  - `siguiente-ticket` instruye invocar la skill `speckit-specify`, que es invocable por el
    modelo (`disable-model-invocation: false`).
  - `/abrir-pr` instruye delegar en el subagente `revisor-codigo` por nombre.
  - `/abrir-pr` lleva `disable-model-invocation: true`: publicar es una decisión del
    desarrollador, así que el modelo no puede dispararlo por su cuenta.
  - `/abrir-pr` **no** pre-aprueba `git push` ni `create_pull_request`: las dos acciones
    que publican piden confirmación al desarrollador cada vez.
- **Rationale**: la invocación por instrucción en lenguaje natural es la documentada. El
  bloqueo de `/abrir-pr` evita publicaciones no pedidas. No pre-aprobar las publicaciones
  agrega una segunda barrera: aunque el revisor fallara y aprobara un cambio con problemas,
  nada se publica sin la confirmación del desarrollador.
- **Alternatives considered**: `context: fork` + `agent: revisor-codigo` en `/abrir-pr`.
  Ejecutaría *todo* el comando dentro del revisor, de solo lectura, y no podría crear el PR.

## R5. Selección del siguiente ticket

- **Decision**: entre los issues en *Todo*, el de menor número cuyas dependencias de
  "**Depende de**" estén cerradas. Se resuelve con `projects_list` (ítems con su `Status`)
  e `issue_read` (cuerpo y estado de las dependencias).
- **Rationale**: el Project no guarda un orden de prioridad consultable. "Menor número con
  dependencias cerradas" es determinista y respeta el grafo del backlog.
- **Alternatives considered**: agregar un campo "Prioridad" al Project. Es más estructura
  sin necesidad; el argumento opcional ya cubre los cambios de orden.

## R6. Rama y numeración

- **Decision**:
  - La skill calcula `NNN` como el siguiente número libre en `specs/`. El `slug` sale del
    título del issue: 2 a 4 palabras en minúsculas, sin tildes.
  - Crea la rama con `git checkout -b NNN-slug` desde `main` actualizado.
  - La carpeta y `.specify/feature.json` los crea `speckit-specify`; sus instrucciones ya
    lo exigen.
- **Rationale**: Spec Kit 1.2 no crea la rama sin su extensión de git. Así se mantiene la
  convención rama = carpeta, y la skill no escribe archivos por su cuenta.
- **Alternatives considered**: instalar la extensión de git de Spec Kit. Es otra pieza más
  que defender para un solo comando.

## R7. Idempotencia de los comandos

- **Decision**: antes de cada acción visible, los comandos consultan el estado actual:
  - **Estado del ítem:** si ya está en el estado destino, no lo mueven.
  - **Comentarios:** buscan un marcador al inicio (`**Inicio del ticket.**`,
    `**PR abierto: #N.**`).
  - **PR:** `list_pull_requests` con `head` de la rama.

  Si la acción ya está hecha, la omiten y lo informan.
- **Rationale**: FR-012. Un reintento tras una falla de red o del MCP no debe duplicar nada.

## R8. Paso a *Done* y regla de PR vinculados

- **Decision**:
  - El paso a *Done* lo hace la regla integrada "Item closed" del Project. No hay GitHub
    Action.
  - La regla "Pull request linked to issue" se desactiva en la interfaz del Project, y
    `/abrir-pr` es el único responsable del paso a *In Review*.
- **Rationale**:
  - La regla integrada ya funciona, verificado con el PR #15 (merge 19:29:55, *Done*
    19:29:57). Una Action duplicaría la responsabilidad y requeriría secretos en el repo.
  - La regla de PR vinculados no actuó en la prueba, y si se activara podría contradecir
    *In Review*. Desactivarla deja una sola fuente de verdad. Solo se configura desde la
    web, así que la desactiva el desarrollador.
- **Alternatives considered**:
  - Configurar la regla para que ponga *In Review*: dos mecanismos para el mismo
    movimiento.
  - Una GitHub Action con token: más piezas y un secreto que gestionar.

## R9. Contenido de los comentarios

- **Decision**: dos plantillas fijas.
  - **Inicio:** rama y siguiente paso.
  - **PR abierto:** qué se especificó (historias y requisitos), qué se decidió (enlace a
    `research.md` y ajustes de los puntos de control) y qué quedó pendiente.
- **Rationale**: el enunciado pide esos tres apartados, y una plantilla fija permite que
  el evaluador compare tickets entre sí.
- **Ajustes de los puntos de control**: `/abrir-pr` los toma de la conversación y de los
  commits de la rama. La plantilla obliga a declararlos aunque no haya ninguno ("Sin
  ajustes").
