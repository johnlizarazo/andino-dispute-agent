# Quickstart: Bloqueo y escalamiento (issue #7)

## Prerrequisitos

- `uv sync` hecho; servidor `core-bancario` aprobado en Claude Code (`.mcp.json`).

## 1. Tests deterministas

```bash
uv run pytest
```

Esperado: todo en verde, incluido `test_bloqueo_escalamiento.py`.

## 2. Verificación en una sesión nueva de Claude Code

Con la app reiniciada (para que `core-bancario` cargue las 6 herramientas):

| Paso | Llamada | Esperado |
|---|---|---|
| 1 | `bloquear_tarjeta` CLI-001, 4821, motivo | `estado` bloqueada, `ya_estaba_bloqueada` falso |
| 2 | `bloquear_tarjeta` CLI-001, 4821 otra vez | éxito, `ya_estaba_bloqueada` verdadero |
| 3 | `bloquear_tarjeta` CLI-004, 9012 | éxito, `ya_estaba_bloqueada` verdadero (dato inicial) |
| 4 | `bloquear_tarjeta` CLI-002, 4821 | validación `NO_ENCONTRADO` |
| 5 | `escalar_a_analista` causa `umbral`, CLI-001, `["TRX-002"]`, acciones y recomendación | `ESC-0001`, monto 1250000 del core, estado `pendiente_analista` |
| 6 | `escalar_a_analista` causa `persona_solicitada`, solo acciones y recomendación | `ESC-0002`, `cliente` null |
| 7 | `escalar_a_analista` sin `accion_recomendada` | validación que nombra el campo |
| 8 | `escalar_a_analista` causa `umbral` sin transacciones | validación |

En el paso 5 se observa además cómo envía la lista el cliente MCP de Claude Code (arreglo o
texto JSON); ambos deben aceptarse.

## 3. Escaneo de datos

`bloquear_pii.py --diff` sobre el diff de la rama contra `main`: sin hallazgos.
