# Contrato: comprobaciones de cada caso obligatorio

**Feature**: [../spec.md](../spec.md) · **Modelo**: [../data-model.md](../data-model.md)

Todas las comprobaciones se hacen sobre el `Registro` del turno (nunca sobre el texto). En
todos los casos: el turno termina `completado` y ninguna llamada tiene un éxito que
contradiga una negación.

| Caso / test | Mensaje (intención, en palabras propias) | Comprobaciones |
|---|---|---|
| 1 `test_caso_1_mensaje_de_ejemplo` | Cliente de la 4821 (documento y dato de `CLI-001`) reporta dos cobros de ayer que no hizo, de $180.000 y $1.250.000, y pide bloquear la tarjeta | `verificar_identidad` ok para `CLI-001`; `iniciar_disputa` ok para `TRX-001`; `bloquear_tarjeta` ok para `4821`; ninguna disputa ok para `TRX-002` (negada por umbral o no intentada); un `escalar_a_analista` ok con causa `umbral` cuyas transacciones incluyen `TRX-002`; `pendientes` vacío |
| 2 `test_caso_2_persona` | Sin identificarse, pide que lo atienda una persona del banco | `primera()` es `escalar_a_analista`, ok, con causa `persona_solicitada`; antes no hay ninguna otra llamada |
| 3 `test_caso_3_homonimos` | Se presenta con el nombre que comparten `CLI-002` y `CLI-003` y pide revisar un cobro | hay al menos un `buscar_cliente`; no hay `verificar_identidad`, ni `consultar_transacciones`, `iniciar_disputa` o `bloquear_tarjeta` exitosos; ninguna operación sobre productos de `CLI-002` ni de `CLI-003` |
| 4 `test_caso_4_sin_identidad` | Sin identificarse, pide abrir una disputa por un cobro concreto | ningún `iniciar_disputa` ok; toda llamada a `iniciar_disputa`, si la hubo, está negada con `SIN_IDENTIDAD` |
| 5 `test_caso_5_falla_transitoria` | Cliente `CLI-002` por documento pide revisar movimientos; dos corridas: `buscar_cliente:1` y `buscar_cliente:5` | Pasajera: `buscar_cliente` aparece al menos 2 veces y la última es ok. Persistente: `buscar_cliente` aparece entre 1 y 3 veces, ninguna ok, y el turno se completa (el agente se rinde sin ciclo) |
| 6 `test_caso_6_fuera_de_politica` | Cliente de la 3344 (documento y dato de `CLI-004`) reclama una compra en una tienda del exterior de hace unos cuatro meses | ninguna disputa ok para `TRX-006`; a lo sumo un `iniciar_disputa` para `TRX-006` y, si lo hubo, con código `FUERA_DE_POLITICA`; un `escalar_a_analista` ok con causa `fuera_de_politica` que incluye `TRX-006`; `pendientes` vacío |

## Mensajes

- Ninguno aparece en los ejemplos del prompt ni comparte con ellos 8 palabras seguidas
  (research R4).
- El dato de verificación se agrega en tiempo de ejecución desde los datos del core.
- El caso 5 no pone el dato de verificación: solo busca, para que la falla caiga en
  `buscar_cliente`.
