# Quickstart: Transacciones y disputas (issue #6)

## Prerrequisitos

- `uv sync` hecho; servidor `core-bancario` aprobado en Claude Code (`.mcp.json`).

## 1. Tests deterministas

```bash
uv run pytest
```

Esperado: todo en verde, incluidos `test_transacciones.py` y los casos nuevos de repositorio,
contexto, servidor e identificación.

## 2. Verificación en una sesión nueva de Claude Code

Con la app reiniciada (para que `core-bancario` cargue las herramientas nuevas). Sustituye
`AYER` por la fecha de ayer en formato `AAAA-MM-DD`.

| Paso | Llamada | Esperado |
|---|---|---|
| 1 | `consultar_transacciones` CLI-001, 4821, `AYER`–`AYER` | 2 cobros: $180.000 y $1.250.000 |
| 2 | `consultar_transacciones` CLI-002, 4821 | validación `NO_ENCONTRADO` |
| 3 | `consultar_transacciones` CLI-001, 4821, desde posterior a hasta | validación `PARAMETRO_INVALIDO` |
| 4 | `iniciar_disputa` TRX-001 con un motivo | `CASO-0001`, monto 180000 |
| 5 | `iniciar_disputa` TRX-001 otra vez | negocio `DISPUTA_EXISTENTE` con `CASO-0001` |
| 6 | `iniciar_disputa` TRX-002 | negocio `REQUIERE_ANALISTA` |
| 7 | `iniciar_disputa` TRX-006 | negocio `FUERA_DE_POLITICA` |
| 8 | `iniciar_disputa` TRX-004 | se abre (umbral inclusivo) |
| 9 | `consultar_transacciones` CLI-001, 4821, `AYER`–`AYER` | TRX-001 con `CASO-0001`, TRX-002 sin caso |

## 3. Escaneo de datos

`bloquear_pii.py --diff` sobre el diff de la rama contra `main`: sin hallazgos.
