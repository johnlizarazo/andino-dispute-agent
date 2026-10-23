"""Servidor MCP ``core-bancario``: simula el core de Banco Andino (ficticio).

``crear_servidor`` arma un ``Contexto`` explícito (repositorio, inyector de fallas, intentos,
disputas, bloqueos y escalamientos) y registra sobre él las seis herramientas de la
constitución: identificación (#5), transacciones (#6) y bloqueo y escalamiento (#7), cada
grupo con su propio ``registrar``.
"""

from mcp.server.fastmcp import FastMCP

from core_bancario_mcp import bloqueo_escalamiento, identificacion, transacciones
from core_bancario_mcp.contexto import Contexto
from core_bancario_mcp.fallas import InyectorFallas, desde_entorno
from core_bancario_mcp.repositorio import Repositorio


def crear_servidor(
    repositorio: Repositorio | None = None, inyector: InyectorFallas | None = None
) -> FastMCP:
    servidor = FastMCP("core-bancario")
    contexto = Contexto(repositorio or Repositorio(), inyector or desde_entorno())
    identificacion.registrar(servidor, contexto)
    transacciones.registrar(servidor, contexto)
    bloqueo_escalamiento.registrar(servidor, contexto)
    return servidor
