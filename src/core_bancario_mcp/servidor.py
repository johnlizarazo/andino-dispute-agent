"""Servidor MCP ``core-bancario``: simula el core de Banco Andino (ficticio).

``crear_servidor`` arma un ``Contexto`` explícito (repositorio, inyector de fallas y control
de intentos) y registra sobre él las herramientas de cada módulo. Las de transacciones,
disputas y bloqueo llegan en los issues #6 y #7 con su propio ``registrar``.
"""

from mcp.server.fastmcp import FastMCP

from core_bancario_mcp import identificacion
from core_bancario_mcp.contexto import Contexto
from core_bancario_mcp.fallas import InyectorFallas, desde_entorno
from core_bancario_mcp.repositorio import Repositorio


def crear_servidor(
    repositorio: Repositorio | None = None, inyector: InyectorFallas | None = None
) -> FastMCP:
    servidor = FastMCP("core-bancario")
    contexto = Contexto(repositorio or Repositorio(), inyector or desde_entorno())
    identificacion.registrar(servidor, contexto)
    return servidor
