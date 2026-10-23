# Data Model: Datos ficticios, contrato de errores e inyección de fallas

Todos los datos son ficticios (principio III). Los formatos exactos de los archivos están en
[contracts/datos.md](contracts/datos.md).

## Cliente

| Campo | Tipo | Regla |
|---|---|---|
| `id` | texto | Único; `CLI-NNN` |
| `nombre` | texto | Puede repetirse: hay dos clientes con el mismo nombre |
| `documento` | texto | `^CC-FIC-\d{4}$`; único |
| `dato_verificacion` | texto | Ficticio (año de nacimiento); distinto de los datos de búsqueda |

## Tarjeta

| Campo | Tipo | Regla |
|---|---|---|
| `id` | texto | Único; `TAR-NNN` |
| `cliente_id` | texto | Debe existir en clientes |
| `ultimos4` | texto | Exactamente 4 dígitos; nunca el número completo |
| `estado` | texto | `activa` o `bloqueada` |

**Estado**: `activa` → `bloqueada` (lo hará `bloquear_tarjeta`, issue #7). Bloquear una tarjeta
ya bloqueada no es error grave. El cambio vive en memoria del servidor.

## Transacción

| Campo | Tipo | Regla |
|---|---|---|
| `id` | texto | Único; `TRX-NNN` |
| `tarjeta_id` | texto | Debe existir en tarjetas |
| `dias_atras` | entero ≥ 0 | La fecha se calcula al cargar: `hoy - dias_atras` |
| `monto` | entero > 0 | Pesos colombianos ficticios, sin decimales |
| `comercio` | texto | Nombre ficticio |
| `pais` | texto | Código ISO de 2 letras (`CO`, `US`, etc.) |
| `estado` | texto | `aplicada` |

**Derivados al cargar**: `fecha` y `cliente_id` (a través de la tarjeta).

## Política

| Campo | Tipo | Regla |
|---|---|---|
| `dias_maximos_disputa_exterior` | entero | 90 |
| `dias_maximos_disputa_nacional` | entero | Ventana nacional (valor ficticio, por ejemplo 120) |
| `umbral_disputa_automatica` | entero | 500000 (informativo; la garantía es el hook del #9) |

## Respuesta del core

- **Éxito**: `{"ok": true, "datos": <cualquier JSON>}`.
- **Error**: `{"ok": false, "error": {"tipo", "codigo", "mensaje", "reintentable"}}`.
- **Regla**: `reintentable == (tipo == "transitorio")`.

## Configuración de fallas

- **Variable**: `CORE_BANCARIO_FALLAS`, con la forma `operacion:N[,operacion:N]` y `N` ≥ 1.
- **Estado en el proceso**: fallas restantes por operación; se descuentan de a una por
  llamada hasta 0.
