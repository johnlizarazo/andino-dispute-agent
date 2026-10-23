# Contrato: servidor `core-bancario`

Fundamento en [research.md R1 y R8](../research.md).

## `servidor.py`

```python
def crear_servidor(repositorio: Repositorio | None = None,
                   inyector: InyectorFallas | None = None) -> FastMCP:
    """FastMCP("core-bancario") con el repositorio y el inyector disponibles para las
    herramientas de los issues #5 a #7. En este ticket no registra herramientas."""
```

## `__main__.py`

Crea el repositorio y el inyector de fallas (este último desde el entorno), construye el
servidor y llama a `run()` (stdio). Si los datos o la configuración de fallas son
inválidos, escribe el error en stderr y sale con código 1 **antes** de servir.

## `.mcp.json` (servidor agregado)

```json
"core-bancario": {
  "type": "stdio",
  "command": "uv",
  "args": ["run", "--no-sync", "python", "-m", "core_bancario_mcp"]
}
```

## Tests (`test_servidor.py`)

- `crear_servidor()` devuelve un servidor llamado `core-bancario` con la lista de
  herramientas vacía.
- **Arranque real por stdio**: lanzar `python -m core_bancario_mcp` con el cliente stdio de
  `mcp`, inicializar la sesión y listar herramientas, con un tiempo límite de 10 s. Debe
  responder en menos de 5 s (SC-005).
- Con `CORE_BANCARIO_FALLAS="op:0"`, el proceso termina con código 1 y un mensaje claro.
