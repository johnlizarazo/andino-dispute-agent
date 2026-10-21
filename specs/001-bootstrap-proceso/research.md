# Research: Bootstrap del proceso

Fase 0 del plan. Cada decisión resuelve una incógnita técnica de la spec. Fuentes: documentación
de Claude Code (`code.claude.com/docs/en/permissions`, `settings`, `settings-reference`,
`mcp`), `github/github-mcp-server` (`docs/remote-server.md`) y una prueba local de `uv_build`.

## R1. Patrones de `permissions.deny` para archivos `.env*`

- **Decision**: reglas de ruta sin ancla, con negación para el ejemplo:
  `Read(.env)`, `Read(.env.*)`, `Read(!.env.example)`, `Edit(.env)`, `Edit(.env.*)`,
  `Edit(!.env.example)`.
- **Rationale**:
  - Los patrones siguen la sintaxis de gitignore. Un nombre sin ancla (`.env`) coincide a
    cualquier profundidad bajo el directorio de trabajo, así que cubre la raíz y las
    subcarpetas.
  - `.env.*` no coincide con `.env`, por eso se necesitan ambas reglas.
  - En los permisos, deny siempre gana: un `allow` no puede abrir una excepción. La única
    excepción posible es una negación `!` en la misma lista de deny, válida solo para reglas
    sin ancla escritas antes de ella.
  - Un deny de `Read` también bloquea Edit y Write sobre la misma ruta, y excluye esos
    archivos de los resultados de Grep y Glob.
- **Alternatives considered**:
  - `Write(...)`: Claude Code acepta la regla pero nunca la consulta, y avisa al arrancar. Las
    escrituras se cubren con `Edit(...)`.
  - Reglas ancladas (`/.env`): solo cubrirían la raíz, y la negación `!` no funciona sobre
    reglas ancladas.
  - Un hook propio que bloquee `.env`: más código para algo que ya resuelve una
    configuración declarativa.

## R2. Comandos de consola sobre `.env*`

- **Decision**: además de R1, reglas de comando para lo que el deny de `Read` no cubre:
  - `Bash(grep * .env*)`, `Bash(cp .env* *)`. No se incluye `type`: en Bash no muestra
    archivos, y en PowerShell es alias de `Get-Content`, ya cubierto.
  - `PowerShell(Get-Content *.env*)`, `PowerShell(Copy-Item *.env* *)`,
    `PowerShell(Select-String * *.env*)`.
- **Rationale**:
  - Según la documentación, el deny de `Read` ya cubre los comandos de lectura que Claude
    Code reconoce en Bash (`cat`, `head`, `tail`, `sed`, `tee`) y las redirecciones. `grep`
    no está en esa lista.
  - PowerShell es una familia de reglas aparte: las reglas `Bash(...)` no la cubren. Los
    alias se normalizan (`gc` y `cat` coinciden con `Get-Content`).
  - En Windows, esta sesión usa las dos consolas.
- **Limitación documentada**: las reglas de comando comparan el texto del comando. No
  detienen `bash -c '...'`, rutas absolutas del binario ni programas que abren el archivo
  por su cuenta. Tampoco admiten negación, así que también bloquean `grep` sobre
  `.env.example` (es aceptable: no contiene secretos). La garantía fuerte es que los
  secretos nunca se versionan (R3); esta capa es de mejor esfuerzo, como dice la spec.
- **Alternatives considered**: sandbox del sistema operativo. Da protección a nivel de
  proceso, pero es más configuración de la que justifica este proyecto. Queda anotado para
  `DECISIONES.md`.

## R3. Exclusiones de git

- **Decision**: `.gitignore` con `.env`, `.env.*`, `!.env.example`, `CLAUDE.local.md`,
  `.claude/settings.local.json`, `.venv/` y cachés de Python.
- **Rationale**: es la garantía fuerte de que ningún secreto llega al repositorio ni al
  `.zip` de entrega. `.specify/.gitignore` ya excluye el estado local de Spec Kit
  (`feature.json`).
- **Alternatives considered**: ignorar `.claude/` entero, como sugiere `specify init`. Se
  descarta porque `.claude/` es donde viven las convenciones del equipo (settings
  compartidos, skills, subagentes, rules); ignorarla rompería "convenciones al clonar".

## R4. Variable `PYTHONUTF8` en el entorno compartido

- **Decision**: `"env": { "PYTHONUTF8": "1" }` en `.claude/settings.json`.
- **Rationale**: la clave `env` define variables "para cada sesión y para los subprocesos
  que Claude Code inicia", lo que incluye los scripts Python de Spec Kit. Los valores se
  copian literalmente. Aplica después de que cada desarrollador confíe en la carpeta.
- **Alternatives considered**:
  - Pedir a cada desarrollador que la defina en su sistema: rompe "cero configuración".
  - Parchear los scripts de Spec Kit: se pierde al actualizar Spec Kit.

## R5. Conexión con el servidor MCP de GitHub

- **Decision**: `.mcp.json` con un servidor `github` de tipo `http`, URL
  `https://api.githubcopilot.com/mcp/` y headers `Authorization: Bearer ${GITHUB_PAT}` y
  `X-MCP-Toolsets: context,repos,issues,pull_requests,projects`.
- **Rationale**:
  - Claude Code expande `${VAR}` en `url` y `headers` de servidores HTTP.
  - `X-MCP-Toolsets` es el header documentado por GitHub para habilitar conjuntos de
    herramientas; `projects` no viene habilitado por defecto.
  - Si `GITHUB_PAT` no está definida, la configuración carga igual, `claude mcp list` avisa
    y se envía el texto literal: la conexión falla de forma visible y no se guarda ningún
    token.
  - Se usa un nombre propio (`GITHUB_PAT`) porque ciertos nombres, como
    `ANTHROPIC_API_KEY`, se leen siempre vacíos en headers.
- **Alternatives considered**:
  - URL con un solo conjunto (`/mcp/x/projects`): admite un único conjunto por URL.
  - Servidor local por Docker o binario: agrega una dependencia de instalación sin beneficio.
  - Un nombre de conjunto mal escrito se ignora en silencio, por eso la verificación (R7)
    prueba una escritura real.

## R6. Dos paquetes con `uv_build`

- **Decision**: `[tool.uv.build-backend] module-name = ["agente_disputas", "core_bancario_mcp"]`,
  con `src/agente_disputas/` y `src/core_bancario_mcp/`. Se elimina el paquete de ejemplo
  `andino_dispute_agent` y su script de consola.
- **Rationale**: probado localmente con `uv` 0.13.2. `uv sync` instala ambos módulos y los
  dos importan sin errores.
- **Alternatives considered**: dos proyectos separados en un workspace de `uv`. Agrega
  estructura sin necesidad: el agente y el servidor comparten versión y dependencias.

## R7. Verificación de escritura en el Project

- **Decision**: con la conexión MCP activa, el asistente mueve el ítem del issue #1 de
  estado (por ejemplo, de *In Progress* a *In Review* y de vuelta) y comenta en el issue.
- **Rationale**: listar herramientas no prueba que el token tenga permiso de projects ni que
  el conjunto `projects` quedó habilitado. Solo una escritura real lo prueba.
- **Alternatives considered**: verificar con `/mcp`. Es necesario, pero no suficiente.

## R8. Finales de línea

- **Decision**: `.gitattributes` con `* text=auto eol=lf` y `*.ps1 text eol=crlf`.
- **Rationale**: en Windows, git avisa que convertirá LF a CRLF. Fijar LF en el repositorio
  evita diffs ruidosos y scripts de hooks que fallen en Linux o macOS. Los scripts de
  PowerShell conservan CRLF por compatibilidad.
- **Alternatives considered**: depender de `core.autocrlf` de cada desarrollador. No es
  reproducible.

## R9. Configuración de pytest

- **Decision**: en `pyproject.toml`, `testpaths = ["src", "tests"]`, el marcador `e2e`
  registrado y `addopts = "-m 'not e2e'"`. Un test de humo por paquete, junto a su código.
- **Rationale**:
  - El principio VI exige que `uv run pytest` esté siempre en verde. Sin tests, pytest
    termina con código 5 ("no tests collected"), que no es verde.
  - Los tests de humo fijan desde el inicio la convención de tests junto al código.
  - Con `addopts` excluyendo `e2e`, `uv run pytest` corre solo lo determinista, y
    `uv run pytest -m e2e` corre los escenarios (el último `-m` gana).
- **Alternatives considered**: no agregar tests hasta el issue #4. Deja `uv run pytest` en
  rojo durante tres tickets y la convención sin fijar.
