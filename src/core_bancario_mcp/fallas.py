"""Inyección de fallas transitorias para el caso de prueba "falla del servidor MCP".

``CORE_BANCARIO_FALLAS="operacion:N[,operacion:N]"`` hace que las primeras N llamadas a esa
operación devuelvan un error transitorio reintentable sin ejecutarla. Es determinista: nada
de probabilidades, para que la demo y los tests sean reproducibles.
"""

import functools
import os

from core_bancario_mcp.errores import Codigo, TipoError, error

VARIABLE = "CORE_BANCARIO_FALLAS"
MENSAJE = (
    "El core bancario no respondió (falla transitoria simulada). Puedes reintentar."
)


class ConfiguracionFallasError(Exception):
    """La configuración de fallas está mal escrita; el core no debe arrancar."""


class InyectorFallas:
    def __init__(self, configuracion: str | None):
        self._restantes: dict[str, int] = {}
        for fragmento in (configuracion or "").split(","):
            fragmento = fragmento.strip()
            if not fragmento:
                continue
            operacion, separador, veces = fragmento.partition(":")
            operacion, veces = operacion.strip(), veces.strip()
            if not separador or not operacion or not veces.lstrip("-").isdigit():
                raise ConfiguracionFallasError(
                    f"{VARIABLE}: fragmento inválido '{fragmento}' "
                    "(formato esperado operacion:N)"
                )
            if int(veces) < 1:
                raise ConfiguracionFallasError(
                    f"{VARIABLE}: '{fragmento}' debe fallar al menos 1 vez"
                )
            self._restantes[operacion] = int(veces)

    def debe_fallar(self, operacion: str) -> bool:
        """True si a la operación le quedan fallas; descuenta una."""
        if self._restantes.get(operacion, 0) > 0:
            self._restantes[operacion] -= 1
            return True
        return False


def desde_entorno() -> InyectorFallas:
    return InyectorFallas(os.environ.get(VARIABLE))


def con_fallas(inyector: InyectorFallas, operacion: str):
    """Decorador: mientras queden fallas, devuelve el error transitorio sin ejecutar."""

    def decorar(funcion):
        @functools.wraps(funcion)
        def envoltura(*args, **kwargs):
            if inyector.debe_fallar(operacion):
                return error(TipoError.TRANSITORIO, Codigo.FALLA_TRANSITORIA, MENSAJE)
            return funcion(*args, **kwargs)

        return envoltura

    return decorar
