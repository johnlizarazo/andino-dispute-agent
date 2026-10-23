# Contrato: política, repositorio, registro y servidor

Fundamento en [research.md R1, R2, R4 y R5](../research.md).

## `repositorio.py`

```python
@dataclass(frozen=True)
class Politica:
    ...
    def requiere_analista(self, monto: int) -> bool: ...        # monto > umbral
    def cubre(self, transaccion: Transaccion, hoy: date) -> bool: ...  # 90 exterior / 120 CO

class Repositorio:
    hoy: date
    def tarjetas_de(self, cliente_id: str, ultimos4: str) -> list[Tarjeta]: ...
```

Tests (`test_repositorio.py`): `requiere_analista(500000)` es falso y `(500001)` verdadero;
`cubre` en los cuatro bordes (90/91 exterior, 120/121 nacional); `repositorio.hoy` es el
inyectado; `tarjetas_de("CLI-001", "4821")` devuelve TAR-001 y `("CLI-002", "4821")` vacío.

## `contexto.py`

```python
@dataclass(frozen=True)
class Caso:
    id: str; transaccion_id: str; monto: int; motivo: str; estado: str

class RegistroDisputas:
    def caso_de(self, transaccion_id: str) -> Caso | None: ...
    def abrir(self, transaccion: Transaccion, motivo: str) -> Caso: ...

@dataclass
class Contexto:
    ...
    disputas: RegistroDisputas = field(default_factory=RegistroDisputas)
```

Tests (`test_contexto.py`): ids secuenciales desde `CASO-0001`; `caso_de` antes y después de
abrir; abrir dos veces la misma transacción lanza `ValueError`; cada `Contexto` tiene su
propio registro.

## `transacciones.py` y `servidor.py`

```python
def consultar_transacciones(contexto, cliente_id=None, ultimos4=None,
                            fecha_desde=None, fecha_hasta=None) -> dict: ...
def iniciar_disputa(contexto, transaccion_id=None, motivo=None) -> dict: ...
def registrar(servidor: FastMCP, contexto: Contexto) -> None: ...
```

`crear_servidor` llama a `identificacion.registrar` y `transacciones.registrar` sobre el mismo
`Contexto`. Tests (`test_servidor.py`): `list_tools` devuelve las 4 herramientas;
descripciones según US4; parámetros publicados como `string`; el arranque por stdio lista las
4 en menos de 5 s.
