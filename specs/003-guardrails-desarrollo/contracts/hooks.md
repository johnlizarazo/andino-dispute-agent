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
- El punto de entrada envuelve todo en `try/except`. Ante cualquier excepción, escribe en
  stderr y sale con 2.
  - En los `PreToolUse` el mensaje es `"<script>: error interno, se bloquea por seguridad:
    <tipo>"`.
  - En `formatear` (`PostToolUse`) es `"formatear: error interno: <tipo>"`, porque ahí no hay
    bloqueo: la edición ya ocurrió.
- Salida 0 sin texto si se permite.

## `bloquear_pii.py`

- **Modo hook**: lee el evento de stdin, extrae los textos nuevos y busca:
  - **Tarjeta**: 13 a 19 dígitos contiguos; o grupos de 4 separados por espacio o guion
    (4-4-4-1…3, 4-4-4-4, 4-4-4-4-1…3); o la forma 4-6-5. Al quitar separadores debe pasar
    Luhn.

    *Ajuste de implementación*: el patrón genérico `(?:\d[ -]?){12,18}\d` podía unir montos
    separados por un espacio ("180000 1250000") y, en un 10% de los casos, pasar Luhn. Exigir
    grupos de 4 refleja cómo se escriben las tarjetas reales.
  - **Documento**: `(?i)(?<!\w)(?:c\.?c\.?|c[eé]dula|documento|nit|pasaporte)(?!\w)\W{0,3}(\d{1,3}(?:\.\d{3}){1,3}|\d{6,10})(?!\d|\.\d)`.
    El cierre `(?!\d|\.\d)` rechaza que siga otro dígito o la continuación de unos miles,
    pero acepta el punto final de una oración. Lo detectó la revisión independiente: un
    cierre `(?![\d.])` dejaba pasar un documento al final de una oración.
  - **Excepción**: `CC-FIC-\d{4}`.
- **Si hay hallazgos**: stderr con `Bloqueado: dato con forma real (<tipo>) en <archivo>,
  línea <n> del texto nuevo: <muestra enmascarada>. Usa datos ficticios (tarjeta: solo últimos 4;
  documento: CC-FIC-NNNN).` y salida 2.
- **Modo CLI** (para CI): `python bloquear_pii.py --diff <archivo_diff>`. Analiza solo las
  líneas agregadas (`+` sin `+++`) de un diff unificado y reporta todos los hallazgos con su
  archivo. Sale con 1 si hay alguno y con 0 si no.
- **Funciones públicas, para los tests**: `luhn_valido(digitos)`, `buscar_hallazgos(texto)` y
  `textos_nuevos(evento)`.

## `exigir_spec.py`

1. Si la ruta (`tool_input.file_path`, o `notebook_path` en NotebookEdit), relativa a
   `CLAUDE_PROJECT_DIR` (o a `cwd`), no empieza por `src/`: sale con 0. La comparación no
   distingue mayúsculas, porque en Windows `SRC/` es la misma carpeta.
2. Obtiene la rama con `git symbolic-ref --short HEAD`. A diferencia de `rev-parse
   --abbrev-ref HEAD`, funciona también en una rama recién creada sin commits. Si no cumple
   `^\d{3}-[a-z0-9-]+$`: bloquea ("escribir en src/ requiere una rama de ticket NNN-slug").
3. Si falta cualquiera de `specs/<rama>/{spec,plan,tasks}.md`: bloquea, nombrando los que
   faltan.

## `formatear.py`

1. Si el archivo no termina en `.py` o no existe: sale con 0.
2. En `CLAUDE_PROJECT_DIR`, ejecuta `uv run --no-sync ruff format <archivo>` y luego
   `uv run --no-sync ruff check --fix <archivo>`. Con `--no-sync`, el hook no reinstala el
   proyecto en cada edición: es más rápido y evita el bloqueo de archivos de `.venv` que
   se observó en Windows.
3. Como los demás hooks, envuelve todo en `try/except`: un error interno se reporta a Claude
   con salida 2. En `PostToolUse` eso es retroalimentación, porque la edición ya ocurrió.
4. Si `ruff check` deja problemas: stderr con su salida y salida 2. Es retroalimentación; la
   edición ya ocurrió.
5. Si `uv` o `ruff` no están disponibles: un aviso en stderr y salida 0, sin bloquear.
