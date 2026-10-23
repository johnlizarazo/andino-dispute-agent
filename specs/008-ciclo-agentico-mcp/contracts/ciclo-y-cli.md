# Contrato: ciclo y línea de comandos

Fundamento en [research.md R2, R5 y R6](../research.md).

## `ciclo.py`

```python
@dataclass(frozen=True)
class ResultadoTurno:
    estado: str; texto: str; herramientas: tuple[str, ...]; detalle: str | None

def clasificar(resultado: ResultMessage) -> str: ...
async def procesar_turno(mensajes: AsyncIterable[Message]) -> ResultadoTurno: ...
def estado_core(respuesta_mcp_status: dict) -> bool: ...
```

`procesar_turno` recorre los mensajes del turno hasta el `ResultMessage` (sin contar ni
buscar palabras), junta el texto de los `TextBlock` de los `AssistantMessage`, anota el nombre
de cada `ToolUseBlock` y devuelve el resultado con `clasificar`. Si el flujo termina sin
`ResultMessage`, el estado es `error`.

Tests (`test_ciclo.py`, mensajes construidos con las clases del SDK):
- `AssistantMessage(stop_reason="tool_use")` con `ToolUseBlock`, `UserMessage` con el
  resultado, `AssistantMessage(stop_reason="end_turn")` con texto y `ResultMessage(subtype=
  "success")` → `completado`, el texto final y la herramienta usada.
- `subtype="error_max_turns"` → `salvaguarda`; `terminal_reason="max_turns"` → `salvaguarda`.
- `is_error=True, api_error_status=529` → `falla_servicio`.
- Otro error → `error`; flujo sin resultado → `error`.
- Un texto del modelo que contenga palabras como "listo" o "fin" no cambia el estado
  (prueba de que no hay búsqueda de palabras).
- `estado_core` es verdadero solo si `core-bancario` figura como `connected`.

## `cli.py` y `__main__.py`

```python
async def conversar(cliente, entrada, salida) -> int: ...   # bucle turno a turno
def main() -> int: ...                                      # python -m agente_disputas
```

- `main`: valida la credencial (falta → mensaje con el nombre de la variable y código 1);
  crea las opciones; conecta; comprueba el core con `estado_core` (no conectado → mensaje y
  código 1); llama a `conversar`; captura `CLINotFoundError`, `CLIConnectionError` y
  `ProcessError` con mensaje claro y código 1; Ctrl+C → despedida y código 0.
- `conversar`: lee una línea; vacía → la ignora; `/salir` o fin de entrada → termina con 0;
  si no, envía el mensaje y muestra según `ResultadoTurno.estado` (tabla del
  [data-model](../data-model.md)).

Tests (`test_cli.py`, con un cliente falso que entrega mensajes preparados):
- Dos mensajes → dos respuestas en orden; la línea vacía no se envía.
- `/salir` y fin de entrada terminan con 0.
- `salvaguarda`, `falla_servicio` y `error` muestran sus avisos sin datos técnicos y el bucle
  sigue.
- Sin `ANTHROPIC_API_KEY`, `main` devuelve 1 y el mensaje nombra la variable.

## Escenario `e2e` (`tests/escenarios/test_conversacion_e2e.py`)

Marcado `@pytest.mark.e2e`, se salta si falta `ANTHROPIC_API_KEY`. Con
`CORE_BANCARIO_FALLAS="buscar_cliente:1"`, el cliente pide ayuda dando un documento ficticio
(mensaje distinto de los ejemplos del prompt): el turno termina `completado`, `buscar_cliente`
aparece al menos dos veces en `herramientas` y la respuesta no contiene detalles técnicos del
error (`FALLA_TRANSITORIA`).
