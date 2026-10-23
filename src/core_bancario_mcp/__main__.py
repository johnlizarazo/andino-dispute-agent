"""Arranca el servidor ``core-bancario`` por stdio: ``python -m core_bancario_mcp``.

Si los datos o la configuración de fallas son inválidos, lo informa y sale con 1 antes de
servir, para no responder con un core a medio cargar.
"""

import sys

from core_bancario_mcp.fallas import ConfiguracionFallasError, desde_entorno
from core_bancario_mcp.repositorio import DatosInvalidosError, Repositorio
from core_bancario_mcp.servidor import crear_servidor


def main() -> int:
    try:
        servidor = crear_servidor(Repositorio(), desde_entorno())
    except (DatosInvalidosError, ConfiguracionFallasError) as error:
        print(f"core-bancario no arrancó: {error}", file=sys.stderr)
        return 1
    servidor.run(transport="stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
