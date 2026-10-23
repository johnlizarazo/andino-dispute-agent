# Contrato: rules por ruta

Fundamento en [research.md R2](../research.md). Ambas van en `.claude/rules/` del
repositorio.

## `.claude/rules/tests.md`

```yaml
---
paths:
  - "src/**/test_*.py"
  - "tests/**/*.py"
  - "plugins/**/test_*.py"
---
```

Contenido (breve, sin repetir la constitución):

- El test vive en la misma carpeta que el módulo y se llama `test_<módulo>.py`.
- Nombres de test en español y descriptivos (`test_<comportamiento>`).
- Tests deterministas: sin red, sin API, sin reloj real. Las fechas relativas se calculan
  respecto de un "hoy" inyectado.
- Los escenarios que llaman al modelo van en `tests/escenarios/` con `@pytest.mark.e2e`, y
  sus mensajes difieren de los ejemplos del prompt.
- Datos solo ficticios. Los números que deban pasar Luhn se generan en el test.

La ruta `plugins/**/test_*.py` se agrega porque los tests de los scripts del plugin siguen la
misma convención.

## `.claude/rules/herramientas-mcp.md`

```yaml
---
paths:
  - "src/core_bancario_mcp/**/*.py"
---
```

Contenido:

- **Respuesta:** toda herramienta devuelve `{"ok": true, "datos": ...}` o
  `{"ok": false, "error": {"tipo", "codigo", "mensaje", "reintentable"}}`.
- **Tipos de error:** `tipo` toma uno de los valores `transitorio`, `validacion`, `negocio`
  o `permiso`.
- **Búsqueda sin resultados:** responde `ok: true` con una lista vacía; no es error.
- **Descripción de cada herramienta:**
  - Para qué sirve y cuándo no usarla.
  - En particular, que buscar no verifica identidad y que, con varias coincidencias, se pide
    otro identificador.
- **Nombres:** herramientas en español, como en la constitución.
