# Data Model: Bootstrap del proceso

Este ticket no maneja datos de negocio. Sus "entidades" son piezas de configuración, con el
alcance (compartido o personal), el lugar donde viven y sus reglas de validación.

## Configuración compartida del asistente

- **Dónde**: `.claude/settings.json` (versionado).
- **Campos**:
  - `permissions.deny`: lista de reglas que niegan acceso a `.env*`. Ver
    [contracts/claude-settings.md](contracts/claude-settings.md).
  - `env.PYTHONUTF8`: `"1"`.
- **Validación**:
  - JSON válido.
  - Ninguna regla `Write(...)`, porque nunca se consultan.
  - La negación `!.env.example` aparece después de las reglas sin ancla que excepciona.
  - Ningún valor de secreto.
- **Relaciones**: lo complementa la configuración personal, que no puede debilitar los deny,
  porque deny siempre gana.

## Configuración personal

- **Dónde**: `CLAUDE.local.md`, `.claude/settings.local.json`, `~/.claude/`.
- **Validación**: `git check-ignore` devuelve coincidencia para los dos archivos del
  repositorio.
- **Ciclo de vida**: la crea cada desarrollador; nunca se versiona.

## Instrucciones del proyecto

- **Dónde**: `CLAUDE.md` (versionado).
- **Contenido**: `@.specify/memory/constitution.md`, comandos clave y flujo con puntos de
  control.
- **Validación**:
  - Breve: menos de 40 líneas.
  - No copia texto de la constitución; solo la importa.

## Conexión MCP de GitHub

- **Dónde**: `.mcp.json` (versionado).
- **Campos**: `mcpServers.github` con `type`, `url` y `headers`. Ver
  [contracts/mcp-json.md](contracts/mcp-json.md).
- **Validación**:
  - El token aparece solo como `${GITHUB_PAT}`.
  - Los conjuntos de herramientas incluyen `projects`.
- **Estados de la conexión**:

  | Estado | Condición | Efecto |
  |---|---|---|
  | Sin token | `GITHUB_PAT` no definida | `claude mcp list` avisa; la conexión falla de forma visible |
  | Solo lectura | Token sin scope `project` | Lee issues, pero no mueve ítems del Project |
  | Operativa | Token con `repo` y `project` | Mueve ítems y comenta (verificación R7) |

## Token de GitHub

- **Dónde**: variable de entorno de usuario `GITHUB_PAT`; nunca en archivos del repositorio.
- **Atributos**: PAT clásico, scopes `repo` y `project`, expiración corta.
- **Validación**: un barrido del historial de git no encuentra el patrón de token
  (`ghp_`, `gho_`, `github_pat_`).

## Variables de entorno declaradas

- **Dónde**: `.env.example` (versionado).
- **Contenido**: `GITHUB_PAT=` y `ANTHROPIC_API_KEY=`, sin valores, con un comentario de
  propósito para cada una.

## Paquetes del proyecto

- **Dónde**: `src/agente_disputas/`, `src/core_bancario_mcp/`.
- **Validación**: ambos importan después de `uv sync`; cada uno tiene un `test_paquete.py`
  junto a su código.
