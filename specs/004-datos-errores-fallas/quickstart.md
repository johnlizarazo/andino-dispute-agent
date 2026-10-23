# Quickstart de validación: Datos ficticios, contrato de errores e inyección de fallas

Para los detalles, ver [contracts/](contracts/).

## 1. Tests deterministas

`uv run pytest`: pasan los tests de `src/core_bancario_mcp/` (errores, repositorio, fallas y
servidor) y los del plugin, incluidos los nuevos de la forma 4-6-5 y de `/dev/null`.

## 2. Datos de los casos (US2)

```bash
uv run python -c "from core_bancario_mcp.repositorio import Repositorio; r = Repositorio(); print([(t.id, t.fecha, t.monto) for t in r.transacciones.values() if t.tarjeta_id == 'TAR-001'])"
```

Esperado: dos transacciones con la fecha de ayer, de 180000 y 1250000.

## 3. Fallas (US3)

```bash
CORE_BANCARIO_FALLAS="op:0" uv run python -m core_bancario_mcp
```

Esperado: termina con código 1 y un mensaje sobre la configuración inválida.

## 4. Servidor registrado (US5)

1. Reiniciar Claude Code y abrir `/mcp`: deben aparecer **`github`** y **`core-bancario`**,
   conectados.
2. `core-bancario` lista 0 herramientas; las de negocio llegan en los issues #5 a #7.

## 5. Datos protegidos

El diff de la rama pasa `bloquear_pii.py --diff` sin hallazgos, y el CI `guardrails` del PR
pasa.
