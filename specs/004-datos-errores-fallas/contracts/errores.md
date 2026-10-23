# Contrato: `core_bancario_mcp/errores.py`

Fundamento en [research.md R2](../research.md).

```python
class TipoError(StrEnum):
    TRANSITORIO = "transitorio"
    VALIDACION = "validacion"
    NEGOCIO = "negocio"
    PERMISO = "permiso"

class Codigo:  # constantes; los issues #5 a #7 agregan las suyas
    FALLA_TRANSITORIA = "FALLA_TRANSITORIA"
    NO_ENCONTRADO = "NO_ENCONTRADO"
    PARAMETRO_INVALIDO = "PARAMETRO_INVALIDO"

def exito(datos) -> dict:
    """{"ok": True, "datos": datos}"""

def error(tipo: TipoError, codigo: str, mensaje: str) -> dict:
    """{"ok": False, "error": {"tipo", "codigo", "mensaje", "reintentable"}},
    con reintentable = (tipo == TipoError.TRANSITORIO)."""
```

## Reglas

- `reintentable` **no** es un parámetro: se deriva del tipo (FR-003).
- `codigo` en MAYÚSCULAS_CON_GUIONES_BAJOS; `mensaje` en español y sin datos sensibles.
- `exito([])` es la respuesta de una búsqueda sin resultados (FR-005).
- `error` rechaza un `tipo` que no sea `TipoError`, para que no puedan aparecer tipos fuera
  del contrato.

## Tests (`test_errores.py`)

- `exito` con un dict, una lista y una lista vacía.
- Para cada `TipoError`, la forma completa del error y el valor de `reintentable`: verdadero
  solo en `transitorio`.
- Un `tipo` inválido lanza `ValueError` o `TypeError`.
