---
paths:
  - "src/core_bancario_mcp/**/*.py"
---

# Convención de herramientas MCP (`core-bancario`)

- Toda herramienta responde `{"ok": true, "datos": ...}` o
  `{"ok": false, "error": {"tipo", "codigo", "mensaje", "reintentable"}}`.
- `tipo` toma uno de los valores `transitorio`, `validacion`, `negocio` o `permiso`.
  `reintentable` es `true` solo para `transitorio`. No lo escribas a mano: usa
  `core_bancario_mcp.errores.exito()` y `error()`, que lo derivan del tipo.
- Una búsqueda sin resultados no es error: `ok: true` con una lista vacía.
- La descripción de cada herramienta dice para qué sirve y cuándo **no** usarla. Para
  `buscar_cliente`: no verifica identidad, y con varias coincidencias se pide otro
  identificador; nunca se elige.
- Nombres de herramientas en español: `buscar_cliente`, `verificar_identidad`,
  `consultar_transacciones`, `iniciar_disputa`, `bloquear_tarjeta`, `escalar_a_analista`.
