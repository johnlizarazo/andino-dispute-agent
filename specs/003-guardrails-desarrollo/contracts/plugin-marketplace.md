# Contrato: plugin, marketplace y consumo

Fundamento en [research.md R3](../research.md).

## `plugins/andino-guardrails/.claude-plugin/plugin.json`

```json
{
  "name": "andino-guardrails",
  "description": "Guardrails de desarrollo para equipos de Banco Andino: bloqueo de datos con forma real, spec-first, formato automático y auditoría de cumplimiento.",
  "author": { "name": "Equipo de disputas, Banco Andino (ficticio)" },
  "keywords": ["guardrails", "pii", "spec-kit", "cumplimiento"]
}
```

Sin `version`, para seguir los commits en vez de fijarse en una copia de la caché.

## `.claude-plugin/marketplace.json` (raíz)

```json
{
  "name": "banco-andino",
  "description": "Plugins compartidos de los equipos de Banco Andino (ficticio).",
  "owner": { "name": "Equipo de disputas, Banco Andino (ficticio)" },
  "plugins": [
    {
      "name": "andino-guardrails",
      "source": "./plugins/andino-guardrails",
      "description": "Guardrails de desarrollo: datos ficticios, spec-first, formato y cumplimiento."
    }
  ]
}
```

## `.claude/settings.json` (cambios)

```json
"extraKnownMarketplaces": {
  "banco-andino": { "source": { "source": "directory", "path": "./" } }
},
"enabledPlugins": { "andino-guardrails@banco-andino": true },
"permissions": { "allow": [ "...existentes...", "Bash(uv run pytest *)" ] }
```

**Fallback (R3)**: si la fuente `directory` no se resuelve, usar
`{"source": "github", "repo": "johnlizarazo/andino-dispute-agent"}` y documentar el
procedimiento de desarrollo.

## Validación

`claude plugin validate ./` y `claude plugin validate ./plugins/andino-guardrails` terminan
sin errores.

## `plugins/andino-guardrails/README.md`

Debe explicar:

- **Qué trae el plugin:** los 3 hooks, el auditor y la skill.
- **Requisitos:** `uv` y `ruff`.
- **Cómo se refresca tras modificarlo:** `/reload-plugins`, o abrir una sesión nueva.
- **La garantía del auditor:** sin herramientas de escritura; los comandos de Bash fuera de
  `allow` piden aprobación.
