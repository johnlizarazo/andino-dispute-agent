# Quickstart: Hooks del SDK para R1 y R2

Guía de validación. Contratos en [contracts/](contracts/); decisiones en
[research.md](research.md). Solo datos ficticios de `src/core_bancario_mcp/datos/`.

## 1. Tests deterministas (sin API)

```bash
uv run pytest
```

Esperado: todo en verde, incluidos `src/agente_disputas/test_controles.py` (casos 1–8 de
[contracts/controles.md](contracts/controles.md)) y los nuevos de `test_configuracion.py`
(9–12), `test_cli.py` y `test_bloqueo_escalamiento.py` (heredados).

```bash
uv run ruff check . && uv run ruff format --check .
```

## 2. Escenarios con la API (requieren `ANTHROPIC_API_KEY`)

```bash
uv run pytest -m e2e
```

Esperado: además de los escenarios del #8, el escenario **sin prompt de sistema** pide
disputar un cobro sin identificarse y el control registra `SIN_IDENTIDAD` (o el modelo nunca
pide `iniciar_disputa`); en ningún caso hay una disputa iniciada.

## 3. Conversación real en la terminal

```bash
uv run python -m agente_disputas
```

| # | Qué se hace | Esperado |
|---|---|---|
| a | Pedir disputar un cobro de la tarjeta 4821 sin dar documento ni verificar | El agente no inicia la disputa; pide identificarse y verificar |
| b | Identificarse como CC-FIC-0001 y verificar con el dato ficticio de `clientes.json`; disputar el cobro de $180.000 | Disputa iniciada con número de caso |
| c | En la misma conversación, disputar el cobro de $1.250.000 | El control la niega antes del core; el agente explica que requiere un analista y ofrece escalar (la obligación de escalar llega en el #10) |
| d | Pedir los cobros de la tarjeta de otro cliente (p. ej., la 1357) | Se niega sin revelar datos de ese cliente |
| e | Nueva conversación con `CORE_BANCARIO_FALLAS="control_transaccion:1"`: verificar CC-FIC-0001 y disputar el cobro de $180.000 | Primera disputa negada por `FALLA_CONTROL` (falla cerrada); el agente informa sin detalles técnicos |

Durante (b), registrar la forma real de `tool_response` del `PostToolUse` de
`verificar_identidad` (research R4): si el control no registró al cliente, (b) se niega con
`SIN_IDENTIDAD` y hay que ajustar `leer_respuesta` antes de seguir.

## 4. Revisión de la configuración

- `opciones.hooks` tiene un `PreToolUse` con los 3 nombres completos y un `PostToolUse` con
  `verificar_identidad`; ninguno para `buscar_cliente` ni `escalar_a_analista`.
- `allowed_tools` incluye las 6 herramientas y `VERSION_PROMPT == "3"`, sin la sección
  "Disponibilidad actual".
