# Quickstart: Identificación (issue #5)

## Prerrequisitos

- `uv sync` hecho; servidor `core-bancario` aprobado en Claude Code (`.mcp.json`).

## 1. Tests deterministas

```bash
uv run pytest
```

Esperado: todo en verde, incluidos `test_identificacion.py`, `test_contexto.py` y los casos
nuevos de repositorio y fallas.

## 2. Verificación en una sesión nueva de Claude Code

Con la app reiniciada (para que `core-bancario` cargue las herramientas nuevas):

| Paso | Llamada | Esperado |
|---|---|---|
| 1 | `buscar_cliente` con nombre "carlos perez" | 2 coincidencias, solo id y nombre |
| 2 | `buscar_cliente` con últimos 4 "4821" | 1 coincidencia (CLI-001) |
| 3 | `buscar_cliente` con documento `CC-FIC-0099` | `ok: true`, lista vacía |
| 4 | `buscar_cliente` sin criterios | validación no reintentable |
| 5 | `verificar_identidad` de CLI-001 con su dato correcto | verificado |
| 6 | `verificar_identidad` de CLI-004 con un dato incorrecto, 3 veces | permiso ×3 |
| 7 | `verificar_identidad` de CLI-004 con el dato correcto | negocio `INTENTOS_AGOTADOS` |

Los datos correctos están en `src/core_bancario_mcp/datos/clientes.json` (ficticios).

## 3. Arranque con configuración inválida

En Bash:

```bash
CORE_BANCARIO_FALLAS="op:1,op:2" uv run --no-sync python -m core_bancario_mcp
```

En PowerShell:

```powershell
$env:CORE_BANCARIO_FALLAS = "op:1,op:2"; uv run --no-sync python -m core_bancario_mcp; Remove-Item Env:CORE_BANCARIO_FALLAS
```

Esperado: `core-bancario no arrancó: ...` y código de salida 1, sin traza.
