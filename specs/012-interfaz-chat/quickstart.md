# Quickstart: Interfaz de chat

**Feature**: [spec.md](spec.md) · **Contratos**: [contracts/](contracts/)

## Requisitos

- Dependencias instaladas: `uv sync`.
- `ANTHROPIC_API_KEY` en el entorno (solo para los pasos 2 y 3).

## 1. Tests deterministas (sin API)

```bash
uv run pytest
```

Esperado: todo en verde, incluidos `test_eventos.py` (cada fila de
[contracts/eventos.md](contracts/eventos.md), negaciones, fallas, respuestas ilegibles y
llamadas sin resultado), `test_sesion.py` (cliente falso: orden de eventos, avisos, estado
por conversación) y `test_controles.py` (`Negacion.tool_use_id`).

## 2. Escenario de punta a punta

```bash
uv run pytest -m e2e tests/escenarios/test_eventos_e2e.py
```

Esperado: conversaciones reales producen los eventos de bloqueo, de negación por umbral
seguida de escalamiento, de disputa iniciada y de escalamiento por pedido de persona, cada
uno en el turno correspondiente.

## 3. Verificación manual en el navegador

```bash
uv run andino-chat
```

Con los datos ficticios del core (clientes y transacciones de `core_bancario_mcp/datos`):

| Caso | Qué escribir (en tus palabras) | Esperado |
|---|---|---|
| Turnos | Dos mensajes seguidos | Cada respuesta debajo de su mensaje; el segundo turno recuerda el primero |
| Bloqueo | Identificarse, verificar y pedir bloquear la tarjeta | ✅ Identidad verificada → ✅ Tarjeta bloqueada `•••• NNNN` |
| Sin identidad | Pedir bloquear sin verificar | ⛔ Operación negada por un control del banco (si el agente intenta la operación) |
| Disputa en umbral | Disputar un cobro ≤ $500.000 | ✅ Disputa iniciada con caso, transacción y monto |
| Disputa sobre umbral | Disputar un cobro > $500.000 | ⛔ negada (umbral) → ✅ Caso escalado a un analista |
| Persona | Pedir hablar con una persona | ✅ Caso escalado a un analista, motivo "el cliente pidió hablar con una persona" |
| Falla | Arrancar con `CORE_BANCARIO_FALLAS` configurado | ⚠️ No se pudo completar, nunca ✅ |
| Sesión nueva | Abrir otra pestaña | Empieza sin identidad verificada |

Prueba de legibilidad (SC-003): pedir a alguien ajeno al proyecto que lea el chat de los casos
de bloqueo y de disputa sobre el umbral y explique qué pasó.
