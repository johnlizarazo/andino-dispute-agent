# Contrato: hooks del plugin

Fundamento en [research.md R4, R5, R7 y R8](../research.md).

## Registro (`plugins/andino-guardrails/hooks/hooks.json`)

```json
{
  "description": "Guardrails de desarrollo de Banco Andino: datos ficticios, spec-first y formato.",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "^(Write|Edit|MultiEdit|NotebookEdit)$",
        "hooks": [
          { "type": "command", "command": "uv run --no-project python \"${CLAUDE_PLUGIN_ROOT}/hooks/bloquear_pii.py\"" },
          { "type": "command", "command": "uv run --no-project python \"${CLAUDE_PLUGIN_ROOT}/hooks/exigir_spec.py\"" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "^(Write|Edit|MultiEdit)$",
        "hooks": [
          { "type": "command", "command": "uv run --no-project python \"${CLAUDE_PLUGIN_ROOT}/hooks/formatear.py\"" }
        ]
      }
    ]
  }
}
```

## Reglas comunes

- Solo biblioteca estándar.
- El punto de entrada envuelve todo en `try/except`. Ante cualquier excepción, escribe
  `"<script>: error interno, se bloquea por seguridad: <tipo>"` en stderr y sale con 2.
- Salida 0 sin texto si se permite.

## `bloquear_pii.py`

- **Modo hook**: lee el evento de stdin, extrae los textos nuevos y busca:
  - **Tarjeta**: 13 a 19 dígitos contiguos; o grupos de 4 separados por espacio o guion
    (4-4-4-1…3, 4-4-4-4, 4-4-4-4-1…3); o la forma 4-6-5. Al quitar separadores debe pasar
    Luhn.

    *Ajuste de implementación*: el patrón genérico `(?:\d[ -]?){12,18}\d` podía unir montos
    separados por un espacio ("180000 1250000") y, en un 10% de los casos, pasar Luhn. Exigir
    grupos de 4 refleja cómo se escriben las tarjetas reales.
  - **Documento**: `(?i)\b(?:c\.?c\.?|c[eé]dula|documento|nit|pasaporte)\b\W{0,3}(\d{1,3}(?:\.\d{3}){1,3}|\d{6,10})(?!\d)`.
  - **Excepción**: `CC-FIC-\d{4}`.
- **Si hay hallazgos**: stderr con `Bloqueado: dato con forma real (<tipo>) en <archivo>
  línea <n>: <muestra enmascarada>. Usa datos ficticios (tarjeta: solo últimos 4;
  documento: CC-FIC-NNNN).` y salida 2.
- **Modo CLI** (para CI): `python bloquear_pii.py --diff <archivo_diff>`. Analiza solo las
  líneas agregadas (`+` sin `+++`) de un diff unificado y reporta todos los hallazgos con su
  archivo. Sale con 1 si hay alguno y con 0 si no.
- **Funciones públicas, para los tests**: `luhn_valido(digitos)`, `buscar_hallazgos(texto)` y
  `textos_nuevos(evento)`.

## `exigir_spec.py`

1. Si `tool_input.file_path`, relativo a `CLAUDE_PROJECT_DIR` (o a `cwd`), no empieza por
   `src/`: sale con 0.
2. Obtiene la rama con `git rev-parse --abbrev-ref HEAD`. Si no cumple
   `^\d{3}-[a-z0-9-]+$`: bloquea ("escribir en src/ requiere una rama de ticket NNN-slug").
3. Si falta cualquiera de `specs/<rama>/{spec,plan,tasks}.md`: bloquea, nombrando los que
   faltan.

## `formatear.py`

1. Si el archivo no termina en `.py` o no existe: sale con 0.
2. En `CLAUDE_PROJECT_DIR`, ejecuta `uv run ruff format <archivo>` y luego
   `uv run ruff check --fix <archivo>`.
3. Si `ruff check` deja problemas: stderr con su salida y salida 2. Es retroalimentación; la
   edición ya ocurrió.
4. Si `uv` o `ruff` no están disponibles: un aviso en stderr y salida 0, sin bloquear.
