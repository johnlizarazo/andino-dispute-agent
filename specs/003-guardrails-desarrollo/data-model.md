# Data Model: Guardrails de desarrollo

No hay datos de negocio. Las entidades son los mensajes que intercambian Claude Code y los
hooks, y los veredictos.

## Evento de hook (entrada por stdin)

- **Campos usados**: `tool_name`, `tool_input.file_path`, `cwd`, y los textos nuevos según
  la herramienta:

  | Herramienta | Campo |
  |---|---|
  | Write | `content` |
  | Edit | `new_string` |
  | MultiEdit | `edits[].new_string` (esquema no verificado) |
  | NotebookEdit | `new_source` |

- **Regla**: el script extrae todo texto nuevo que encuentre. Si no puede leer el JSON,
  bloquea (fallo cerrado).

## Hallazgo de datos

- **Campos**: `tipo` (`tarjeta` o `documento`), `archivo`, `linea` y `muestra`, que es el
  valor enmascarado con solo los últimos 4 dígitos (`•••• 1234`).
- **Validación**: nunca contiene el valor completo (FR-004).

## Resultado de hook

| Código | Significado |
|---|---|
| 0 | Permitido; sin salida |
| 2 | Bloqueado (`PreToolUse`) o retroalimentación (`PostToolUse`); el motivo va por stderr |

Ningún otro código es válido: todo error se convierte en 2.

## Veredicto de cumplimiento

- **Formato**:

  ```text
  VEREDICTO: APROBADO | BLOQUEADO
  BLOQUEANTES: - <archivo>:<línea> — <descripción> (<principio/regla>)
  NO BLOQUEANTES: ...
  NO APLICA: - <regla> — <motivo>
  TESTS: <resumen de uv run pytest>
  ```

- **Regla**: `BLOQUEADO` si y solo si hay al menos un bloqueante, o si los tests
  deterministas fallan.

## Artefactos del ticket

- `specs/<rama>/{spec.md, plan.md, tasks.md}`.
- La rama cumple `^\d{3}-[a-z0-9-]+$`.
