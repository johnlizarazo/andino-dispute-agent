# Data Model: Plugin, marketplace y DECISIONES.md

**Feature**: [spec.md](spec.md) · **Research**: [research.md](research.md)

No hay entidades persistentes; el modelo describe lo que maneja el script de entrega y la
estructura de `DECISIONES.md`.

## Hallazgo (`scripts/armar_entrega.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `tipo` | texto | `github`, `anthropic`, `aws` o `clave_privada` |
| `ubicacion` | texto | Ruta del archivo versionado o `commit <sha corto>` del historial |

Nunca guarda ni muestra el valor encontrado.

## Resultado de la entrega

| Campo | Tipo | Regla |
|---|---|---|
| `ruta` | ruta | `dist/entrega-andino-dispute-agent.zip` por omisión; solo existe si todo pasó |
| `bytes` | entero | Tamaño final; falla si `>= 50 MB`, aviso si `> 40 MB` |
| `archivos` | entero | Cantidad de entradas del `.zip` |
| `hallazgos` | lista de `Hallazgo` | Vacía para que la entrega sea válida |

Exclusiones: `.venv/`, `.env*` salvo `.env.example`, `__pycache__/`, `.pytest_cache/`,
`.ruff_cache/`, `node_modules/`, `*.egg-info/`, `dist/`, `build/`, `.chainlit/`, `.files/`,
`CLAUDE.local.md`, `.claude/settings.local.json`.

## Decisión (`DECISIONES.md`)

| Campo | Regla |
|---|---|
| Necesidad | Qué problema resuelve la pieza |
| Mecanismo | Pieza del ecosistema (hook, skill, subagente, regla, …) |
| Dónde | Ruta en el repositorio |
| Alternativa descartada | Qué se descartó y por qué, en una frase |
| Origen | Enlace al `research.md` del ticket |
