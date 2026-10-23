# Contrato: datos ficticios (`core_bancario_mcp/datos/`)

Fundamento en [research.md R3 y R4](../research.md) y [data-model.md](../data-model.md).
Todos los nombres, comercios, documentos y años son inventados.

## `clientes.json`

| id | nombre | documento | dato_verificacion |
|---|---|---|---|
| CLI-001 | Laura Méndez Ríos | CC-FIC-0001 | 1987 |
| CLI-002 | Carlos Andrés Pérez | CC-FIC-0002 | 1975 |
| CLI-003 | Carlos Andrés Pérez | CC-FIC-0003 | 1992 |
| CLI-004 | Marta Lucía Gómez | CC-FIC-0004 | 1980 |

CLI-002 y CLI-003 tienen el mismo nombre (caso de ambigüedad).

## `tarjetas.json`

| id | cliente_id | ultimos4 | estado |
|---|---|---|---|
| TAR-001 | CLI-001 | 4821 | activa |
| TAR-002 | CLI-002 | 1357 | activa |
| TAR-003 | CLI-003 | 2468 | activa |
| TAR-004 | CLI-004 | 9012 | bloqueada |
| TAR-005 | CLI-004 | 3344 | activa |

## `transacciones.json`

| id | tarjeta_id | dias_atras | monto | comercio | pais | Para qué caso |
|---|---|---|---|---|---|---|
| TRX-001 | TAR-001 | 1 | 180000 | Tienda Ficticia Uno | CO | Mensaje de ejemplo (bajo el umbral) |
| TRX-002 | TAR-001 | 1 | 1250000 | Electro Ficticio | CO | Mensaje de ejemplo (sobre el umbral) |
| TRX-003 | TAR-001 | 10 | 45000 | Café Imaginario | CO | Historial normal |
| TRX-004 | TAR-002 | 5 | 500000 | Viajes Inventados | CO | Borde exacto del umbral (#9) |
| TRX-005 | TAR-003 | 3 | 75000 | Librería Ficticia | CO | Historial del homónimo |
| TRX-006 | TAR-005 | 120 | 320000 | Tienda Exterior Ficticia | US | Exterior con más de 90 días (no cubierto) |
| TRX-007 | TAR-004 | 15 | 90000 | Farmacia Inventada | CO | Tarjeta ya bloqueada (#7) |

Todas con `estado: "aplicada"`. Cada archivo es una lista JSON de objetos con exactamente
estos campos.

## `politicas.json`

```json
{
  "dias_maximos_disputa_exterior": 90,
  "dias_maximos_disputa_nacional": 120,
  "umbral_disputa_automatica": 500000
}
```

## Reglas

- Ninguna tarjeta tiene más de 4 dígitos; ningún documento sale del formato `CC-FIC-NNNN`.
- Los archivos se escriben con el hook `bloquear_pii` activo. Si bloquea, el dato está mal.
