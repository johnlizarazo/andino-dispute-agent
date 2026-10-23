# Research: Guardrails de desarrollo

Fase 0 del plan. Fuentes: documentación de Claude Code (`plugins/manifest-reference`,
`plugins/marketplace-reference`, `plugins/loading`, `hooks`, `memory`, `sub-agents`,
`skills`), consultada el 2026-10-23, y lo aprendido en los issues #1 y #2.

## R1. Mecanismo por necesidad

| Necesidad (spec) | Mecanismo | Dónde |
|---|---|---|
| Datos con forma real (US1) | Hook `PreToolUse` + job de CI con el mismo script | Plugin + `.github/workflows/` |
| Spec-first (US2) | Hook `PreToolUse` | Plugin |
| Formato (US3) | Hook `PostToolUse` | Plugin |
| Cumplimiento (US4) | Subagente `auditor-cumplimiento` + skill `revisar-cumplimiento` | Plugin |
| Convenciones por ruta (US5) | Rules con `paths` | `.claude/rules/` del repo |
| Reutilización (US6) | Plugin `andino-guardrails` + marketplace `banco-andino` | `plugins/` + `.claude-plugin/` |

- **Rationale**: lo que no puede fallar (datos, spec-first, formato) va en hooks, que son
  deterministas. La revisión de cumplimiento necesita juicio, así que va en un subagente
  aislado. Las convenciones son contexto y no garantías, así que van en rules.
- **Alternatives considered**: instrucciones en `CLAUDE.md` para spec-first y datos. No son
  deterministas, lo que viola el principio II.

## R2. Las rules no pueden ir en el plugin

- **Decision**: `tests.md` y `herramientas-mcp.md` van en `.claude/rules/` del repositorio.
- **Rationale**: la estructura documentada de un plugin no tiene `rules/`. Además, las
  convenciones son de este proyecto; otro equipo tendría las suyas.
- **Alternatives considered**: una skill con las convenciones. Se carga por relevancia, no
  por ruta, así que no cumple "aplica solo a estos archivos".

## R3. Cómo consume el repo su propio plugin

- **Decision**: en `.claude/settings.json`:
  - `extraKnownMarketplaces.banco-andino` con fuente `{"source": "directory", "path": "./"}`.
  - `enabledPlugins: {"andino-guardrails@banco-andino": true}`.
- **Rationale**:
  - Con fuente de directorio, un plugin de ruta relativa **se carga en el lugar**. Los
    cambios en la rama se ven con `/reload-plugins` o en la sesión siguiente, sin cambiar la
    versión. Eso es lo que necesita el desarrollo.
  - Con fuente `github`, el plugin se copia a la caché desde la rama remota: los cambios de
    una rama sin fusionar no se verían.
  - `extraKnownMarketplaces` aplica tras aceptar la confianza de la carpeta, lo que cumple
    FR-019.
- **Riesgo**: la documentación no confirma que `path: "./"` se resuelva respecto de la raíz
  del proyecto. Se verifica en la implementación (quickstart §1).
- **Fallback**: fuente `github` con `repo: johnlizarazo/andino-dispute-agent`, documentando
  que los cambios del plugin se ven después del merge (o con `claude plugin marketplace add`
  local durante el desarrollo).
- **Sin `version` en `plugin.json`**: así el plugin sigue los commits y no se queda fijado en
  una copia de la caché.

## R4. Contrato de los hooks y fallo cerrado

- **Decision**:
  - Scripts en Python con solo la biblioteca estándar.
  - Se invocan con `uv run --no-project python "${CLAUDE_PLUGIN_ROOT}/hooks/<script>.py"`.
  - Leen el JSON de stdin. Bloquean con **código de salida 2** y el motivo por stderr.
  - Matcher `^(Write|Edit|MultiEdit|NotebookEdit)$`.
- **Rationale**:
  - En `PreToolUse`, el código 2 bloquea y el motivo llega a Claude.
  - **Cualquier otro código distinto de 0 no bloquea**: la herramienta sigue. Para fallar
    cerrado (FR-005), el script envuelve todo en `try/except` y sale con 2 ante cualquier
    error.
  - Campos de entrada:
    - Write: `tool_input.content`.
    - Edit: `tool_input.new_string`.
    - MultiEdit (no verificado): `tool_input.edits[].new_string`.
    - NotebookEdit: `tool_input.new_source`.

    El script extrae todos los textos nuevos que encuentre, sin depender de un solo esquema.
  - `uv run --no-project` evita depender de un `python` en el PATH y no instala el proyecto
    en cada llamada. En Windows, los hooks corren por Git Bash.
  - Solo biblioteca estándar: el plugin funciona en el repositorio de otro equipo sin
    dependencias.
- **Alternatives considered**:
  - JSON `permissionDecision: deny`: también es válido, pero el código 2 es más simple y
    sirve igual en la CLI de CI.
  - Scripts de shell: no son portables entre Windows y Linux.

## R5. Detección de datos con forma real

- **Decision**:
  - **Tarjeta**: grupos de dígitos separados opcionalmente por espacio o guion que sumen de
    13 a 19 dígitos, delimitados por límites de palabra, y que pasen Luhn.
  - **Documento**: una palabra de documento (`CC`, `C.C.`, `cédula`/`cedula`, `documento`,
    `NIT`, `pasaporte`, sin distinguir mayúsculas) seguida, a lo sumo a 3 caracteres no
    alfanuméricos, de 6 a 10 dígitos (admitiendo puntos de miles).
  - **Excepción**: el formato `CC-FIC-\d{4}`.
  - **Mensaje**: tipo, archivo y número de línea; el valor se enmascara mostrando solo los
    últimos 4 dígitos.
- **Rationale**:
  - Luhn descarta el 90% de las secuencias largas al azar (identificadores, marcas de
    tiempo).
  - Exigir la palabra de documento evita bloquear montos como `1250000`.
  - Enmascarar evita que el propio mensaje filtre el dato.
- **Alternatives considered**: bloquear toda secuencia de 13 o más dígitos. Da falsos
  positivos con hashes e identificadores, y `create-new-feature.ps1` contiene
  `9223372036854775808`.

## R6. Control en GitHub para commits externos

- **Decision**:
  - Un workflow `.github/workflows/guardrails.yml` que corre en cada `pull_request` y en cada
    `push` a `main`.
  - Ejecuta el **mismo** script en modo CLI sobre las líneas agregadas del diff
    (`git diff --unified=0 <base>...HEAD`) y luego `uv run pytest`.
  - Sin secretos.
- **Rationale**:
  - Un pre-commit local exige que cada desarrollador lo instale, lo que rompe "cero
    configuración al clonar". El job de CI cubre todo cambio que llegue a GitHub.
  - Revisar solo el diff evita falsos positivos heredados de archivos de terceros (los
    scripts de Spec Kit).
  - Un solo script garantiza la misma regla dentro y fuera del asistente.
- **Alternatives considered**:
  - Pre-commit: depende de la instalación local.
  - Escanear todo el árbol: hereda ruido de archivos que no son nuestros.

## R7. Spec-first

- **Decision**: el hook de spec-first actúa solo si `tool_input.file_path`, relativo a
  `CLAUDE_PROJECT_DIR`, empieza por `src/`. Obtiene la rama con `git rev-parse
  --abbrev-ref HEAD` y bloquea si la rama no cumple `^\d{3}-[a-z0-9-]+$` o si falta
  `spec.md`, `plan.md` o `tasks.md` en `specs/<rama>/`. Ante un error, bloquea.
- **Rationale**: es la misma convención rama = carpeta que usan `siguiente-ticket` y
  `/abrir-pr`.
- **Alternatives considered**: leer `.specify/feature.json`. Está ignorado por git y puede
  apuntar a otra feature; la rama es la fuente de verdad.

## R8. Formato

- **Decision**: un hook `PostToolUse` con el mismo matcher. Si el archivo es `.py`, ejecuta
  `uv run ruff format <archivo>` y `uv run ruff check --fix <archivo>` en
  `CLAUDE_PROJECT_DIR`.
  - Si quedan problemas, sale con código 2 y los envía por stderr. Claude los ve, y la
    edición no se revierte porque ya ocurrió.
  - Si `ruff` no está disponible, avisa por stderr con salida 0: no bloquea.
- **Rationale**: en `PostToolUse` la herramienta ya se ejecutó, así que el código 2 sirve
  como canal de retroalimentación (FR-011).
- **Alternatives considered**: formatear solo en CI. La retroalimentación llega tarde.

## R9. Auditor en un plugin: sin `permissionMode`

- **Decision**:
  - `auditor-cumplimiento` va en el plugin con `tools: Read, Grep, Glob, Bash`.
  - `permissions.allow` del proyecto agrega `Bash(uv run pytest *)`.
  - Las instrucciones lo limitan a leer y correr tests.
- **Rationale**:
  - La documentación dice que los agentes de plugins **ignoran** `permissionMode`, `hooks` y
    `mcpServers` por seguridad. No se puede repetir la solución `dontAsk` del revisor.
  - Garantía real: sin Write ni Edit en `tools`, no edita archivos con herramientas. Un
    comando Bash fuera de `allow` y fuera de los de solo lectura pide aprobación al
    desarrollador, así que no puede modificar nada **sin aprobación humana**.
  - Es más débil que la garantía del revisor, y se documenta así.
- **Alternatives considered**:
  - Dejar el auditor en `.claude/agents/` con `dontAsk`: es más fuerte, pero entonces el
    plugin necesitaría otro subagente para cumplir el mínimo, y el auditor es justamente la
    pieza reutilizable por otro equipo del banco.
  - Auditor sin Bash: no podría correr los tests.

## R10. Skill de cumplimiento

- **Decision**: `revisar-cumplimiento` en el plugin con:
  - `context: fork` y `agent: andino-guardrails:auditor-cumplimiento`.
  - `background: false`, para que `/abrir-pr` espere el veredicto en el mismo turno.
  - `allowed-tools: Read, Grep, Glob, Bash(uv run pytest *)`.
  - `argument-hint: "[ruta o módulo opcional]"`.
- **Rationale**: con `context: fork` corre aislada y sin el historial, como exige la
  independencia del auditor. `background: false` es necesario porque `/abrir-pr` decide con
  el veredicto.
- **Riesgo**: no está verificado que `agent:` acepte un agente con espacio de nombres del
  plugin. Se prueba (quickstart §5).
- **Fallback**: `agent: general-purpose`, con las instrucciones completas del auditor dentro
  de la skill.

## R11. Integración en `/abrir-pr`

- **Decision**: un paso 2b nuevo, después de la revisión de código: invocar
  `andino-guardrails:revisar-cumplimiento` sobre la rama. Si el veredicto es `BLOQUEADO`, el
  comando se detiene sin publicar. El comentario de avance incluye el veredicto de
  cumplimiento.
- **Rationale**: FR-015. Se cumple lo previsto en `contracts/abrir-pr.md` del issue #2
  ("Extensión prevista").

## R12. Tests de los scripts

- **Decision**:
  - Tests junto a cada script: `plugins/andino-guardrails/hooks/test_*.py`, agregando
    `plugins` a `testpaths`.
  - Los números de tarjeta válidos se generan con una función que calcula el dígito de Luhn
    sobre prefijos aleatorios. El repositorio no tiene ningún literal de tarjeta (FR-006).
- **Rationale**: es el principio VI. Además, el propio hook de datos bloquearía un literal.
