# Contrato: `.claude/settings.json`

Configuración compartida de Claude Code para todo el equipo. Fundamento en
[research.md R1, R2, R4](../research.md).

## Forma esperada

```json
{
  "permissions": {
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(!.env.example)",
      "Edit(.env)",
      "Edit(.env.*)",
      "Edit(!.env.example)",
      "Bash(grep * .env*)",
      "Bash(cp .env* *)",
      "Bash(type .env*)",
      "PowerShell(Get-Content *.env*)",
      "PowerShell(Copy-Item *.env* *)",
      "PowerShell(Select-String * *.env*)"
    ]
  },
  "env": {
    "PYTHONUTF8": "1"
  }
}
```

## Garantías

| Vía de acceso a `.env*` | Cubierta por |
|---|---|
| Herramienta Read | `Read(...)` |
| Herramientas Edit y Write | `Edit(...)` (y el deny de `Read`) |
| Grep y Glob | `Read(...)`: los archivos negados se excluyen de los resultados |
| `cat`, `head`, `tail`, `sed`, `tee` y redirecciones en Bash | `Read(...)`, según la documentación |
| `grep`, `cp`, `type` en Bash | `Bash(...)` |
| `Get-Content` (y alias `gc`, `cat`), `Copy-Item`, `Select-String` en PowerShell | `PowerShell(...)` |

## Fuera de garantía (documentado)

- Comandos que no nombran el archivo (`grep -r clave .`), `bash -c '...'`, rutas absolutas
  del binario y programas que abren el archivo por su cuenta.
- Las reglas de comando no admiten negación, así que también bloquean `.env.example` por
  esas vías.

## Reglas del contrato

- No se usan reglas `Write(...)`.
- Cada negación `!` va después de las reglas sin ancla que excepciona.
- El archivo no contiene valores secretos ni rutas personales.
