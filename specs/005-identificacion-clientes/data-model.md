# Data Model: Identificación (issue #5)

Las entidades `Cliente` y `Tarjeta` son las del [data-model del #4](../004-datos-errores-fallas/data-model.md);
este ticket no cambia los datos. Se agregan:

## Contexto

| Campo | Tipo | Origen |
|---|---|---|
| `repositorio` | `Repositorio` | `crear_servidor` (o el test) |
| `inyector` | `InyectorFallas` | `crear_servidor` (o el test) |
| `intentos` | `IntentosVerificacion` | nuevo por servidor |

Uno por proceso del servidor; lo comparten todas las herramientas.

## IntentosVerificacion

- Estado: `dict[cliente_id, fallos_consecutivos]`, vacío al arrancar.
- `MAXIMO = 3`.
- Transiciones por cliente:

```text
0 ──fallo──> 1 ──fallo──> 2 ──fallo──> 3 (agotado: todo intento → negocio)
│            │            │
└──éxito─────┴──éxito─────┴──> 0
```

Un cliente agotado no vuelve a 0 mientras el proceso siga vivo. Fallas transitorias y
clientes inexistentes no cambian el estado.

## Coincidencia de búsqueda

| Campo | Tipo | Nota |
|---|---|---|
| `cliente_id` | texto | p. ej. `CLI-002` |
| `nombre` | texto | tal como está en los datos |

Nunca incluye `documento` ni `dato_verificacion` (FR-003). Lista ordenada por `cliente_id`.

## Resultado de verificación

| Campo | Tipo |
|---|---|
| `cliente_id` | texto |
| `verificado` | `true` |

## Validaciones de entrada

| Entrada | Regla | Error |
|---|---|---|
| criterios de búsqueda | exactamente uno, texto no vacío ni de solo espacios | validación `PARAMETRO_INVALIDO` |
| `documento` | `^CC-FIC-[0-9]{4}$` (sin espacios en los extremos) | validación `PARAMETRO_INVALIDO` |
| `nombre` | 2+ letras tras normalizar, hasta 100 caracteres | validación `PARAMETRO_INVALIDO` |
| `ultimos4` | `^[0-9]{4}$` | validación `PARAMETRO_INVALIDO` |
| `cliente_id`, `dato_verificacion` | textos presentes y no vacíos | validación `PARAMETRO_INVALIDO` |
| `cliente_id` inexistente | — | validación `NO_ENCONTRADO` |
