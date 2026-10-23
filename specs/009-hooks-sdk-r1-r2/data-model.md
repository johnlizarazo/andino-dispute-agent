# Data Model: Hooks del SDK para R1 y R2

Todo vive en memoria del proceso del agente, por conversación. Fundamento en
[research.md](research.md) R3 a R6.

## EstadoSesion

| Campo | Tipo | Regla |
|---|---|---|
| `cliente_verificado` | `str \| None` | `None` al empezar; lo fija solo un `verificar_identidad` exitoso y legible para el mismo `cliente_id` pedido; un nuevo éxito lo reemplaza; un fallo no lo cambia |
| `negaciones` | `list[Negacion]` | se agrega una por cada operación negada, en orden |

Ciclo de vida: nace con `crear_opciones` (una por conversación) y desaparece con ella.

```text
sin verificar ──verificar ok (cliente X)──▶ verificado X ──verificar ok (cliente Y)──▶ verificado Y
      ▲  └──verificar falla / ilegible──┘          └──verificar falla──▶ (sigue X)
      └────────────────── fin de la conversación (estado nuevo) ──────────────────┘
```

## Negacion

| Campo | Tipo | Valores |
|---|---|---|
| `herramienta` | `str` | nombre completo `mcp__core-bancario__...` |
| `codigo` | `str` | `SIN_IDENTIDAD`, `CLIENTE_DISTINTO`, `TRANSACCION_NO_CONFIRMADA`, `REQUIERE_ANALISTA`, `FALLA_CONTROL` |

## Decision

Resultado puro de evaluar una operación, antes de traducirlo a la salida del hook:

| Campo | Tipo | Regla |
|---|---|---|
| `autorizada` | `bool` | `True` solo si pasan identidad, titularidad y (para disputar) umbral |
| `codigo` | `str \| None` | uno de los códigos de `Negacion` cuando se niega |
| `razon` | `str \| None` | texto en español para el modelo; nunca incluye datos de otro cliente |

## Controles

| Campo | Tipo | Origen |
|---|---|---|
| `estado` | `EstadoSesion` | nuevo por conversación |
| `buscar_transaccion` | `Callable[[str], Transaccion \| None]` | `Repositorio.obtener_transaccion` envuelto con el inyector (`control_transaccion`); función que siempre falla si el repositorio no cargó |
| `politica` | `Politica \| None` | `Repositorio.politica`; `None` si no cargó (toda disputa → `FALLA_CONTROL`) |

Datos leídos (no modificados) de `core_bancario_mcp.repositorio`: `Transaccion.cliente_id`,
`Transaccion.monto` y `Politica.umbral_disputa_automatica` (500000).
