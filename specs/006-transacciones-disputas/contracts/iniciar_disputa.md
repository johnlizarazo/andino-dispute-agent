# Contrato: `iniciar_disputa`

Fundamento en [research.md R1, R3 y R5](../research.md).

## Parámetros (tipo `Texto`, con `None` por omisión)

| Parámetro | Formato |
|---|---|
| `transaccion_id` | id devuelto por `consultar_transacciones` |
| `motivo` | por qué el cliente no reconoce el cobro; hasta 500 caracteres |

No hay parámetro de monto: el monto sale del core (regla 2).

## Respuestas (en este orden de evaluación)

1. Transitorio `FALLA_TRANSITORIA` (`iniciar_disputa:N`); no abre caso.
2. Validación `PARAMETRO_INVALIDO`: tipo no texto, vacío o motivo de más de 500 caracteres.
3. Validación `NO_ENCONTRADO`: la transacción no existe.
4. Negocio `DISPUTA_EXISTENTE`: ya hay caso; el mensaje incluye su `caso_id`.
5. Negocio `FUERA_DE_POLITICA`: la antigüedad supera 90 días (exterior) o 120 (nacional); el
   mensaje dice la antigüedad, el límite y que se escale a un analista.
6. Negocio `REQUIERE_ANALISTA`: el monto supera $500.000; el mensaje dice el umbral y que se
   escale a un analista.
7. Éxito: `{"ok": true, "datos": {"caso_id": "CASO-0001", "transaccion_id", "monto",
   "estado": "abierta"}}`.

Ningún error de 2 a 6 es reintentable ni abre caso.

## Descripción publicada (esencia)

Abre una disputa sobre un cobro que el cliente no reconoce y devuelve el número de caso.
Requiere la identidad verificada del titular. El monto lo toma el core de sus datos. Si el
core responde `FUERA_DE_POLITICA` o `REQUIERE_ANALISTA`, no reintentes: el caso debe
escalarse a un analista. Si responde `DISPUTA_EXISTENTE`, informa el caso que ya existe.

## Tests (`test_transacciones.py`)

- TRX-001 ($180.000) → `CASO-0001` con monto 180000; una segunda disputa → `CASO-0002`.
- TRX-004 ($500.000) → se abre.
- TRX-007 (tarjeta bloqueada) → se abre.
- TRX-001 dos veces → `DISPUTA_EXISTENTE` con `CASO-0001` en el mensaje.
- TRX-006 (exterior, 120 días) → `FUERA_DE_POLITICA`.
- TRX-002 ($1.250.000) → `REQUIERE_ANALISTA`; luego `consultar_transacciones` lo muestra sin
  caso.
- Bordes de política con datos en `tmp_path`: exterior de 90 y 91 días; nacional de 120 y 121.
- Fuera de política **y** sobre el umbral (datos en `tmp_path`) → `FUERA_DE_POLITICA`.
- `TRX-999` → `NO_ENCONTRADO`; motivo vacío, de 501 caracteres o numérico → validación.
