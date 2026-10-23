# Contrato: `buscar_cliente`

Fundamento en [research.md R1, R4 y R5](../research.md).

## Parámetros (todos de tipo `Texto`, research R5; exactamente uno con valor)

| Parámetro | Formato |
|---|---|
| `documento` | `CC-FIC-NNNN` |
| `nombre` | una o más palabras, sin importar mayúsculas ni tildes |
| `ultimos4` | 4 dígitos |

## Respuestas

- Éxito, siempre lista (vacía si no hay coincidencias):
  `{"ok": true, "datos": [{"cliente_id": "CLI-002", "nombre": "..."}, ...]}`
- Validación `PARAMETRO_INVALIDO`: ningún criterio, más de uno, mal formado o que no es
  texto (p. ej. un número). El mensaje
  explica el formato esperado.
- Transitorio `FALLA_TRANSITORIA`: inyectada con `CORE_BANCARIO_FALLAS=buscar_cliente:N`.

## Descripción publicada (esencia)

Busca clientes por **un** criterio: documento, nombre o últimos 4 de tarjeta. **No verifica
identidad**: después de encontrar a un único cliente hay que usar `verificar_identidad`. Si
hay varias coincidencias, **no elijas**: pide al cliente otro identificador (documento o
últimos 4 de su tarjeta) y busca de nuevo. Una lista vacía significa que no hay
coincidencias, no un error.

## Tests (`test_identificacion.py`)

- Documento existente → 1 coincidencia; últimos 4 existentes → el titular.
- "Carlos Andrés Pérez", "carlos perez" y "CARLOS ANDRES PEREZ" → las 2 coincidencias.
- Palabra parcial ("an") no coincide con "Andrés"; "Pérez," (con puntuación) sí coincide.
- Criterio sin coincidencias → `exito([])`.
- Ninguna coincidencia tiene `documento` ni `dato_verificacion` (todas las búsquedas).
- Sin criterio, dos criterios, criterio de solo espacios, documento con otro formato,
  últimos 4 con letras o 3 dígitos, últimos 4 como número o lista, nombre de 1 letra →
  validación no reintentable.
- Últimos 4 compartidos por dos clientes (datos en `tmp_path`) → ambos, sin repetir.
