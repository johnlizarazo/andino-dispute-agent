# Quickstart: Escalamiento con criterio y solicitudes múltiples

Guía de validación. Contratos en [contracts/](contracts/); decisiones en
[research.md](research.md). Solo datos ficticios de `src/core_bancario_mcp/datos/`.

## 1. Tests deterministas (sin API)

```bash
uv run pytest
```

```bash
uv run ruff check . && uv run ruff format --check .
```

Esperado: todo en verde, incluidos los casos de
[contracts/escalamiento-pendiente.md](contracts/escalamiento-pendiente.md) (1–7, el mensaje de
ejemplo en el 6) y de [contracts/prompt-y-descripcion.md](contracts/prompt-y-descripcion.md).

## 2. Escenarios con la API ya existentes

```bash
uv run pytest -m e2e
```

Esperado: los escenarios del #8 y el #9 siguen en verde con el prompt v4 (los escenarios nuevos
del #10 se automatizan en el #13).

## 3. Validación manual (requiere `ANTHROPIC_API_KEY`)

```bash
uv run python -m agente_disputas
```

Cada caso en una conversación nueva. Los mensajes son distintos de los ejemplos del prompt.

| # | Caso | Mensajes (en orden) | Esperado |
|---|---|---|---|
| a | Mensaje de ejemplo | Identificarse como CC-FIC-0001 y verificar; decir que no reconoce los dos cobros de ayer de la tarjeta 4821 y que quiere bloquearla | Disputa del cobro de $180.000 (número de caso), bloqueo de la 4821, la disputa de $1.250.000 negada y escalada con causa umbral (número de escalamiento); **una sola** respuesta con los tres resultados |
| b | Persona desde el primer mensaje | Primer mensaje pidiendo hablar con un asesor humano | `escalar_a_analista` con `persona_solicitada` como **única** herramienta del turno; respuesta con el número de escalamiento |
| c | Fuera de política | Identificarse como CC-FIC-0004 y verificar; pedir disputar el cobro del exterior de hace unos meses de la tarjeta 3344 | La disputa responde fuera de política y el caso se escala con causa `fuera_de_politica` y resumen completo |
| d | Negativo de persona | "Alguien me clonó la tarjeta…" tras verificarse | No escala por persona solicitada; bloquea u ofrece revisar cobros |
| e | Tope del `Stop` | Como (a), con `CORE_BANCARIO_FALLAS="escalar_a_analista:5"` | Tras dos cierres impedidos el turno termina y la línea de comandos muestra el aviso de escalamiento pendiente |

Registrar en cada caso las herramientas del turno y los pendientes al final (como la sonda del
#9).
