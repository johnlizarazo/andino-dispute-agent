# Andino Dispute Agent

Agente de primer contacto para disputas de transacciones y contracargos de **Banco Andino**,
un banco **ficticio**. Está construido con Claude Agent SDK y consume un servidor MCP propio
(`core-bancario`) que simula el core bancario.

> Todos los datos del proyecto son ficticios. No hay datos reales de clientes, cuentas ni
> tarjetas en ningún archivo, log ni configuración.

- **Backlog**: [GitHub Project](https://github.com/users/johnlizarazo/projects/1)
- **Principios del proyecto**: [constitución](.specify/memory/constitution.md)
- **Video de funcionamiento**: _pendiente_

## Requisitos

- Python 3.14 y [`uv`](https://docs.astral.sh/uv/) 0.13 o superior
- [Claude Code](https://code.claude.com/)
- Variables de entorno de usuario `GITHUB_PAT` y `ANTHROPIC_API_KEY` (ver
  [`.env.example`](.env.example) y la sección siguiente)

## Instalación y tests

```bash
uv sync
uv run pytest            # tests deterministas (sin llamadas a la API)
uv run pytest -m e2e     # tests de escenario (requieren ANTHROPIC_API_KEY)
```

## Token de GitHub

Claude Code se conecta al servidor MCP de GitHub ([`.mcp.json`](.mcp.json)) para leer y
actualizar los issues y el Project. El archivo solo referencia `${GITHUB_PAT}`: el token
nunca se escribe en el repositorio.

1. **Crear el token**: GitHub → Settings → Developer settings → Personal access tokens →
   **Tokens (classic)**, con los scopes `repo` y `project`. Los tokens fine-grained no
   cubren bien los Projects de una cuenta personal. Usa una expiración corta.
2. **Guardarlo como variable de entorno de usuario** `GITHUB_PAT`, nunca en un archivo del
   repositorio ni en `.env`. En Windows, desde PowerShell, este comando pide el token sin
   mostrarlo y no lo deja en el historial:

   ```powershell
   $t = Read-Host "Pega el PAT" -AsSecureString; [Environment]::SetEnvironmentVariable("GITHUB_PAT", [System.Net.NetworkCredential]::new("", $t).Password, "User"); Remove-Variable t
   ```

   En Linux o macOS, expórtala desde tu perfil de shell (por ejemplo, `~/.bashrc` o
   `~/.zshrc`).
3. **Reiniciar la aplicación por completo**, incluido el ícono de la bandeja del sistema,
   para que Claude Code herede la variable. Con `/mcp` verás el servidor `github` conectado.

Si el token no tiene el scope `project`, el asistente podrá leer issues pero no mover
ítems del Project.

## Convenciones para quien clona

Al abrir el repositorio con Claude Code se cargan automáticamente:

- [`CLAUDE.md`](CLAUDE.md), que importa la constitución.
- [`.claude/settings.json`](.claude/settings.json), con permisos que impiden leer o editar
  `.env*` y el modo UTF-8 que necesitan los scripts de Spec Kit.
- [`.mcp.json`](.mcp.json), con la conexión a GitHub.

Tus preferencias personales van en `CLAUDE.local.md` o en `.claude/settings.local.json`;
ambos están en `.gitignore`.
