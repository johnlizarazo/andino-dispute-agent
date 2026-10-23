# Contrato: `verificar_identidad`

Fundamento en [research.md R3, R5 y R6](../research.md).

## Parámetros (`str | None`, ambos obligatorios para la herramienta)

| Parámetro | Formato |
|---|---|
| `cliente_id` | id devuelto por `buscar_cliente` |
| `dato` | dato de verificación que da el cliente (año ficticio) |

## Respuestas (en este orden de evaluación)

1. Transitorio `FALLA_TRANSITORIA` si hay falla inyectada (`verificar_identidad:N`); no
   cuenta como intento.
2. Validación `PARAMETRO_INVALIDO` si falta o está vacío algún parámetro.
3. Validación `NO_ENCONTRADO` si el cliente no existe; no cuenta como intento.
4. Negocio `INTENTOS_AGOTADOS` si el cliente ya acumuló 3 fallos consecutivos, aunque el
   dato sea correcto. El mensaje indica escalar a un analista.
5. Éxito `{"ok": true, "datos": {"cliente_id": "CLI-001", "verificado": true}}` si el dato
   coincide exactamente; reinicia el contador.
6. Permiso `VERIFICACION_FALLIDA` si no coincide; suma un fallo. El mensaje no revela el
   dato correcto.

Ninguno de los errores 2 a 6 es reintentable.

## Descripción publicada (esencia)

Confirma la identidad de un cliente con un dato que solo él conoce. Úsala **después** de que
`buscar_cliente` devolvió **una única** coincidencia. Si falla, no reintentes con otro dato
inventado: pide al cliente que lo confirme. Tras 3 fallos el core bloquea la verificación y
hay que escalar.

## Tests (`test_identificacion.py`)

- Dato correcto → verificado; incorrecto → permiso no reintentable sin el dato en el
  mensaje.
- Cliente inexistente → validación `NO_ENCONTRADO`.
- 3 fallos → el cuarto intento con el dato correcto es negocio no reintentable.
- 2 fallos + éxito → el contador vuelve a 0 (3 fallos más para agotar).
- Los fallos de un cliente no afectan a otro.
- Falla inyectada → transitoria y el contador no cambia.
