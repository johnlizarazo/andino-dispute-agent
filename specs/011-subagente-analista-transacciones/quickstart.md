# Quickstart: Subagente `analista-transacciones`

Guía de validación. Contratos en [contracts/](contracts/); decisiones en
[research.md](research.md). Solo datos ficticios.

## 1. Tests deterministas (sin API)

```bash
uv run pytest
```

```bash
uv run ruff check . && uv run ruff format --check .
```

Esperado: todo en verde, incluidos los casos 1–8 de
[contracts/subagente.md](contracts/subagente.md).

## 2. Sonda de la delegación (requiere `ANTHROPIC_API_KEY`)

Script temporal (fuera del repositorio) que arma el agente, se verifica como CC-FIC-0001 y pide
analizar los cobros de ayer de la tarjeta 4821, registrando cada entrada de hook:

- nombre de la herramienta de delegación y campos de su entrada (`subagent_type`, `prompt`);
- que la consulta del subagente llega al `PreToolUse` con `agent_id`;
- que la delegación no dispara `UserPromptSubmit` (los pendientes no se vacían);
- el bloque `<analisis>` devuelto: `TRX-001` disputable y `TRX-002` sobre umbral.

## 3. Escenarios con la API

```bash
uv run pytest -m e2e
```

Esperado: los escenarios anteriores y `test_delegacion_e2e.py` en verde.

## 4. Conversación real

```bash
uv run python -m agente_disputas
```

| # | Caso | Esperado |
|---|---|---|
| a | Verificarse como CC-FIC-0001 y pedir revisar los cobros de ayer de la 4821 | Delega, informa el cobro menor como disputable y el mayor como sobre umbral; disputa el menor y escala el mayor si el cliente lo pide |
| b | Verificarse como CC-FIC-0004 y pedir revisar los cobros de los últimos seis meses de la 3344 | El cobro del exterior de 120 días sale fuera de política y se escala si el cliente quiere reclamarlo |
| c | Sin verificarse, pedir que analicen los cobros de una tarjeta | No delega (control `SIN_IDENTIDAD`) y pide verificar |
