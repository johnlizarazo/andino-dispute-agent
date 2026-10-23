# andino-guardrails

Plugin de Claude Code con garantías de desarrollo para equipos de Banco Andino (ficticio).
Se publica en el marketplace `banco-andino` de este repositorio.

## Qué trae

| Pieza | Tipo | Qué hace |
|---|---|---|
| `bloquear_pii` | Hook `PreToolUse` | Bloquea escrituras con forma de tarjeta (13 a 19 dígitos que pasan Luhn) o de documento real (número junto a "CC", "cédula", "documento"…). Permite montos y el formato ficticio `CC-FIC-NNNN`. Falla cerrado. También funciona como CLI para CI: `bloquear_pii.py --diff cambios.diff`. |
| `exigir_spec` | Hook `PreToolUse` | Bloquea escrituras bajo `src/` si la rama no es `NNN-slug` o le faltan `spec.md`, `plan.md` o `tasks.md` en `specs/<rama>/`. Falla cerrado. |
| `formatear` | Hook `PostToolUse` | Ejecuta `ruff format` y `ruff check --fix` sobre cada `.py` editado; devuelve a Claude lo que no se corrige solo. |
| `auditor-cumplimiento` | Subagente | Verifica la constitución del proyecto (reglas de negocio, garantías deterministas, datos ficticios) y corre los tests deterministas. |
| `revisar-cumplimiento` | Skill (`context: fork`) | Ejecuta al auditor en un contexto aislado y devuelve `APROBADO` o `BLOQUEADO`. Invócala con `/andino-guardrails:revisar-cumplimiento [ruta]`. |

## Requisitos

- [`uv`](https://docs.astral.sh/uv/) en el PATH: los hooks se ejecutan con `uv run --no-project python`.
- `ruff` en el entorno del proyecto (por ejemplo, en el grupo `dev` y `uv sync`). Sin él,
  `formatear` avisa y no bloquea.
- Los scripts solo usan la biblioteca estándar de Python.

## Instalación en otro repositorio

En `.claude/settings.json` del repositorio consumidor:

```json
{
  "extraKnownMarketplaces": {
    "banco-andino": {
      "source": { "source": "github", "repo": "johnlizarazo/andino-dispute-agent" }
    }
  },
  "enabledPlugins": { "andino-guardrails@banco-andino": true }
}
```

La prueba de instalación en otro repositorio y su documentación completa son del issue #14.

## Refrescar tras modificar el plugin

En este repositorio el marketplace es de directorio y el plugin se carga en el lugar:
ejecuta `/reload-plugins` o abre una sesión nueva. Si el marketplace se consume desde GitHub,
el plugin se copia a la caché y los cambios llegan con `claude plugin marketplace update
banco-andino` después del merge.

## Garantías y límites

- Los hooks bloquean con código de salida 2 y convierten cualquier error interno en un
  bloqueo.
- Los agentes de plugins ignoran `permissionMode`, así que **el auditor no puede usar
  `dontAsk`**. Su garantía es no tener herramientas de escritura (`tools: Read, Grep, Glob,
  Bash`). Un comando de Bash fuera de los permitidos por el proyecto o de los de solo lectura
  pide aprobación humana. Es una garantía más débil que la del revisor de código, que vive en
  `.claude/agents/` con `dontAsk`.
- Los hooks revisan las herramientas de escritura de Claude Code. Lo escrito por otros
  medios lo cubre el job de CI `guardrails`.
