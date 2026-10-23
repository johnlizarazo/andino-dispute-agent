# Contrato: contexto y servidor

Fundamento en [research.md R1 a R3](../research.md).

## `contexto.py`

```python
class IntentosVerificacion:
    MAXIMO = 3
    def agotados(self, cliente_id: str) -> bool: ...
    def registrar_fallo(self, cliente_id: str) -> None: ...
    def reiniciar(self, cliente_id: str) -> None: ...

@dataclass
class Contexto:
    repositorio: Repositorio
    inyector: InyectorFallas
    intentos: IntentosVerificacion = field(default_factory=IntentosVerificacion)
```

## `identificacion.py`

```python
def buscar_cliente(contexto, documento=None, nombre=None, ultimos4=None) -> dict: ...
def verificar_identidad(contexto, cliente_id=None, dato=None) -> dict: ...
def registrar(servidor: FastMCP, contexto: Contexto) -> None:
    """Publica ambas herramientas con su descripción, envueltas en con_fallas."""
```

## `servidor.py`

```python
def crear_servidor(repositorio=None, inyector=None) -> FastMCP:
    """FastMCP("core-bancario") con las herramientas de identificación registradas sobre un
    Contexto explícito. No agrega atributos a FastMCP."""
```

`__main__.py` no cambia.

## Tests

- `test_contexto.py`: transiciones de `IntentosVerificacion` (data-model).
- `test_servidor.py`: `list_tools` devuelve exactamente `buscar_cliente` y
  `verificar_identidad`, con descripciones que cumplen US3; el arranque real por stdio lista
  las mismas 2 herramientas en menos de 5 s; `call_tool` responde JSON con el contrato.
