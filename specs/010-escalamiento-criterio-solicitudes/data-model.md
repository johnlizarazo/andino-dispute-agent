# Data Model: Escalamiento con criterio y solicitudes múltiples

Amplía `EstadoSesion` del #9 (en memoria, por conversación). Fundamento en
[research.md](research.md) R2 a R4.

## EstadoSesion (campos nuevos)

| Campo | Tipo | Regla |
|---|---|---|
| `pendientes` | `dict[str, str]` (transacción → causa) | causa en `umbral`, `fuera_de_politica`; una entrada por transacción; se vacía al recibir un mensaje del cliente |
| `cierres_impedidos` | `int` | veces que se impidió terminar el turno actual; 0 al recibir un mensaje; máximo `MAXIMO_CIERRES_IMPEDIDOS = 2` |

Campos del #9 sin cambios: `cliente_verificado`, `negaciones`.

## Ciclo de un pendiente

```text
            negación por umbral (control)  ─┐
 (nada) ──  rechazo FUERA_DE_POLITICA /     ├──▶ pendiente(TRX, causa)
            REQUIERE_ANALISTA (core)       ─┘          │
                                                       ├─ escalar ok con TRX y misma causa ──▶ (nada)
                                                       ├─ escalar falla / sin TRX / otra causa ──▶ sigue
                                                       ├─ Stop con cierres < 2 ──▶ bloquea, cierres += 1
                                                       ├─ Stop con cierres = 2 ──▶ deja terminar (aviso visible)
                                                       └─ nuevo mensaje del cliente ──▶ (nada), cierres = 0
```

## Decision (campo nuevo)

| Campo | Tipo | Regla |
|---|---|---|
| `pendiente` | `str \| None` | id de la transacción cuando la negación es `REQUIERE_ANALISTA`; si no, `None` |

## Constantes

| Nombre | Valor |
|---|---|
| `MAXIMO_CIERRES_IMPEDIDOS` | 2 |
| `UMBRAL`, `FUERA_DE_POLITICA` | `"umbral"`, `"fuera_de_politica"` (mismos valores que las causas de `escalar_a_analista`) |
| `HERRAMIENTA_DESCONOCIDA` | `"desconocida"` |
