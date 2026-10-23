# Contrato: prompt y configuración

Fundamento en [research.md R1, R3 y R4](../research.md).

## `prompts.py`

```python
VERSION_PROMPT: str          # p. ej. "1"; se sube al cambiar el texto
PROMPT_SISTEMA: str
```

El prompt orienta, en español: rol (agente de primer contacto de Banco Andino, ficticio);
las 5 reglas de negocio; cuándo usar cada herramienta (buscar no verifica; con varias
coincidencias pedir otro identificador; verificar antes de operar sobre productos; el monto lo
pone el core; bloquear es inmediato; escalar con resumen y la causa correcta); no inventar
datos ni montos; y cómo actuar ante errores: `reintentable: true` → reintentar la misma
llamada hasta 2 veces y luego informar sin detalles técnicos y ofrecer escalar;
`reintentable: false` → no repetir y actuar según `tipo` (validación: corregir o pedir el
dato; permiso: pedir confirmación; negocio: seguir el mensaje, p. ej. escalar).

Tests (`test_prompts.py`): el prompt menciona las 6 herramientas, el umbral "$500.000",
"reintentable" y "dos veces"; `VERSION_PROMPT` no está vacío.

## `configuracion.py`

```python
HERRAMIENTAS: tuple[str, ...]  # los 6 nombres del core
MODELO_POR_OMISION = "claude-sonnet-5-5"
MAXIMO_PASOS_POR_TURNO = 25    # salvaguarda (FR-006), no control del ciclo

class CredencialFaltanteError(Exception): ...

def validar_credencial(entorno: Mapping[str, str]) -> None: ...
def crear_opciones(entorno: Mapping[str, str]) -> ClaudeAgentOptions: ...
```

Tests (`test_configuracion.py`, sin API):
- `tools == []`, `permission_mode == "dontAsk"`, `strict_mcp_config is True`,
  `setting_sources == []`, `max_turns == 25`.
- `allowed_tools` es exactamente `mcp__core-bancario__` + las 6 herramientas.
- `mcp_servers` tiene solo `core-bancario`, de tipo stdio, con `sys.executable` y
  `-m core_bancario_mcp`.
- `CORE_BANCARIO_FALLAS` se pasa en el `env` del servidor solo si está en el entorno.
- `model` es `claude-sonnet-5-5` por omisión y `ANDINO_MODELO` lo cambia.
- `system_prompt` es `PROMPT_SISTEMA`.
- `validar_credencial` lanza `CredencialFaltanteError` sin `ANTHROPIC_API_KEY` o con ella
  vacía, y el mensaje nombra la variable pero nunca incluye un valor.
