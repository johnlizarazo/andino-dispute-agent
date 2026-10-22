# Contrato: exclusiones de git y finales de línea

Fundamento en [research.md R3 y R8](../research.md).

## `.gitignore`: entradas obligatorias

```gitignore
# Entornos y cachés de Python
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/

# Secretos (nunca se versionan)
.env
.env.*
!.env.example

# Configuración personal de Claude Code
CLAUDE.local.md
.claude/settings.local.json
```

**Verificación**:
- `git check-ignore` devuelve coincidencia para `.env`, `.env.local`, `config/.env`,
  `CLAUDE.local.md` y `.claude/settings.local.json`.
- No devuelve coincidencia para `.env.example`.

**Lo que no se ignora:** la carpeta `.claude/`, porque contiene las convenciones del equipo.

## `.gitattributes`

```gitattributes
* text=auto eol=lf
*.ps1 text eol=crlf
```

**Verificación**: después de `git add --renormalize .`, `git ls-files --eol` muestra `i/lf`
para los archivos de texto, salvo `.ps1`.
