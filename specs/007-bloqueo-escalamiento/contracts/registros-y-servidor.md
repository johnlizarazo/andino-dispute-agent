# Contrato: registros, tipos y servidor

Fundamento en [research.md R1 y R3](../research.md).

## `contexto.py`

```python
class RegistroBloqueos:
    def estado_de(self, tarjeta: Tarjeta) -> str: ...          # "activa" | "bloqueada"
    def bloquear(self, tarjeta: Tarjeta, motivo: str) -> bool: ...  # ¿ya estaba bloqueada?

@dataclass(frozen=True)
class Escalamiento:
    id: str; causa: str; cliente_id: str | None; transacciones: tuple[str, ...]
    acciones_realizadas: str; accion_recomendada: str; estado: str

class RegistroEscalamientos:
    def registrar(self, causa, cliente_id, transacciones, acciones_realizadas,
                  accion_recomendada) -> Escalamiento: ...
    def todos(self) -> list[Escalamiento]: ...

@dataclass
class Contexto:
    ...
    bloqueos: RegistroBloqueos = field(default_factory=RegistroBloqueos)
    escalamientos: RegistroEscalamientos = field(default_factory=RegistroEscalamientos)
```

Tests (`test_contexto.py`): estado inicial respetado (TAR-004 bloqueada, TAR-001 activa);
`bloquear` devuelve `False` y luego `True`; `ESC-0001`, `ESC-0002` secuenciales; cada
`Contexto` tiene sus propios registros.

## `identificacion.py`

```python
ListaTexto = Annotated[object, WithJsonSchema({"type": "array", "items": {"type": "string"}})]
```

## `bloqueo_escalamiento.py` y `servidor.py`

```python
def bloquear_tarjeta(contexto, cliente_id=None, ultimos4=None, motivo=None) -> dict: ...
def escalar_a_analista(contexto, causa=None, cliente_id=None, transacciones=None,
                       acciones_realizadas=None, accion_recomendada=None) -> dict: ...
def registrar(servidor: FastMCP, contexto: Contexto) -> None: ...
```

`crear_servidor` registra identificación, transacciones y bloqueo/escalamiento sobre el mismo
`Contexto`. Tests (`test_servidor.py`): las 6 herramientas de la constitución en `list_tools`
y por stdio; descripciones según US3; `transacciones` publicado como `array` de `string` y el
resto como `string`; `call_tool` con tipo incorrecto responde el contrato.
