# Contrato: `core_bancario_mcp/fallas.py`

Fundamento en [research.md R6](../research.md).

```python
VARIABLE = "CORE_BANCARIO_FALLAS"

class ConfiguracionFallasError(Exception): ...

class InyectorFallas:
    def __init__(self, configuracion: str | None): ...
        # "op:N[,op:N]"; None o "" = sin fallas; inválida = ConfiguracionFallasError
    def debe_fallar(self, operacion: str) -> bool: ...
        # True y descuenta 1 si a la operación le quedan fallas

def desde_entorno() -> InyectorFallas: ...   # lee os.environ[VARIABLE]

def con_fallas(inyector: InyectorFallas, operacion: str):
    """Decorador: si inyector.debe_fallar(operacion), devuelve
    error(TipoError.TRANSITORIO, Codigo.FALLA_TRANSITORIA, "...") sin ejecutar la función."""
```

## Reglas

- **Formato**: `operacion:N`, separados por comas, con espacios tolerados alrededor. `N` es
  un entero ≥ 1.
- **Configuración inválida**: sin `:`, `N` no numérico o `N` ≤ 0 lanzan
  `ConfiguracionFallasError` con un mensaje que cita el fragmento inválido.
- **Mensaje de la falla**: `"El core bancario no respondió (falla transitoria simulada).
  Puedes reintentar."`.
- **Aislamiento**: el contador es propio de cada `InyectorFallas`. El servidor usa uno
  creado al arrancar.

## Tests (`test_fallas.py`)

- `"op:2"`: tres llamadas devuelven `True`, `True` y `False`.
- Sin configuración, `debe_fallar` siempre devuelve `False`.
- `"a:1,b:2"` es independiente por operación.
- Configuraciones inválidas (`"op"`, `"op:x"`, `"op:0"`, `"op:-1"`) lanzan la excepción.
- El decorador devuelve el error transitorio reintentable y no ejecuta la función mientras
  queden fallas; después, la ejecuta.
