# Contrato: `core_bancario_mcp/repositorio.py`

Fundamento en [research.md R4, R5 y R7](../research.md).

```python
@dataclass(frozen=True)
class Cliente:  id, nombre, documento, dato_verificacion
@dataclass(frozen=True)
class Tarjeta:  id, cliente_id, ultimos4, estado
@dataclass(frozen=True)
class Transaccion:  id, tarjeta_id, cliente_id, fecha: date, monto: int, comercio, pais, estado
@dataclass(frozen=True)
class Politica:  dias_maximos_disputa_exterior, dias_maximos_disputa_nacional, umbral_disputa_automatica

class DatosInvalidosError(Exception): ...

class Repositorio:
    def __init__(self, hoy: date | None = None, carpeta: Path | None = None): ...
        # carga los 4 JSON (por defecto del paquete), valida y resuelve fechas
    clientes: dict[str, Cliente]
    tarjetas: dict[str, Tarjeta]
    transacciones: dict[str, Transaccion]
    politica: Politica
    def obtener_transaccion(self, transaccion_id: str) -> Transaccion | None: ...
```

## Reglas

- Las fechas se calculan una vez: `fecha = hoy - timedelta(days=dias_atras)`.
- `cliente_id` de una transacción se deriva de su tarjeta.
- **Validación** (lanza `DatosInvalidosError`, nombrando el archivo y el `id`):
  - Falta un campo o sobra uno.
  - `ultimos4` no tiene 4 dígitos.
  - El documento no cumple `^CC-FIC-\d{4}$`.
  - Hay ids duplicados.
  - Una referencia está rota.
  - `monto` ≤ 0 o `dias_atras` < 0.
  - Falta un archivo o el JSON es inválido.
- `obtener_transaccion` devuelve `None` si el id no existe. No lanza excepciones por un id
  inexistente.
- `carpeta` permite a los tests usar datos de prueba mal formados en `tmp_path`.

## Tests (`test_repositorio.py`)

- **Fechas**: con `hoy = 2027-01-01`, TRX-001 y TRX-002 quedan en `2026-12-31`, con montos
  180000 y 1250000 en la tarjeta `4821`. Con `hoy = 2026-03-01`, "ayer" es el 28 de febrero.
- **Homónimos**: dos clientes con el mismo nombre y documentos distintos.
- **Fuera de política**: TRX-006 tiene país distinto de CO y más de 90 días.
- **Casos de borde de otros tickets**: hay un cobro de exactamente 500000 y una tarjeta
  bloqueada.
- **Consulta por id**: `obtener_transaccion("TRX-002")` devuelve monto, cliente CLI-001 y
  fecha; un id inexistente devuelve `None`.
- **Montos**: todos coinciden con `transacciones.json` (SC-006).
- **Validación**: un test por regla, con JSON mal formados escritos en `tmp_path`.
