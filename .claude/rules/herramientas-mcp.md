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
- Cada módulo de herramientas expone `registrar(servidor, contexto)` y recibe el estado
  (repositorio, fallas, intentos, disputas, bloqueos, escalamientos) por
  `core_bancario_mcp.contexto.Contexto`;
  nunca como atributos agregados a `FastMCP`. La lógica va en funciones puras sobre el
  contexto, que es lo que prueban los tests.
- Los parámetros se declaran con el tipo `Texto` de `identificacion.py` (esquema `string`,
  validación en la herramienta) y valor por defecto `None`, para que ausencias, formatos y
  tipos JSON incorrectos se respondan con el contrato y no con un error de FastMCP.
  Los parámetros de lista usan `ListaTexto` (esquema `array` de `string`); la herramienta
  acepta una lista o un texto con una lista JSON, y responde `PARAMETRO_INVALIDO` a lo demás.
- Una herramienta exenta de identidad verificada (`buscar_cliente`, `verificar_identidad`,
  `escalar_a_analista`) no devuelve datos de productos (montos, fechas, comercios).
- Nombres de herramientas en español: `buscar_cliente`, `verificar_identidad`,
  `consultar_transacciones`, `iniciar_disputa`, `bloquear_tarjeta`, `escalar_a_analista`.
