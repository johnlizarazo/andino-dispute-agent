"""Servidor MCP ``core-bancario``: simula el core de Banco Andino (ficticio).

En este ticket el servidor no expone herramientas; las de negocio (``buscar_cliente``,
``consultar_transacciones``, etc.) llegan en los issues #5 a #7 y usarán el repositorio y
el inyector de fallas que se le pasan aquí.
"""

from mcp.server.fastmcp import FastMCP

from core_bancario_mcp.fallas import InyectorFallas, desde_entorno
from core_bancario_mcp.repositorio import Repositorio


def crear_servidor(
    repositorio: Repositorio | None = None, inyector: InyectorFallas | None = None
) -> FastMCP:
    servidor = FastMCP("core-bancario")
    servidor.repositorio = repositorio or Repositorio()
    servidor.inyector = inyector or desde_entorno()
    return servidor
