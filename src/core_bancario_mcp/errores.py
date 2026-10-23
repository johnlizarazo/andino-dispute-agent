"""Contrato de respuestas del core bancario (principio V de la constitución).

Toda herramienta responde ``exito(datos)`` o ``error(tipo, codigo, mensaje)``. El campo
``reintentable`` no es un parámetro: se deriva del tipo, así que un error de validación,
negocio o permiso nunca puede marcarse como reintentable.
"""

from enum import StrEnum


class TipoError(StrEnum):
    TRANSITORIO = "transitorio"
    VALIDACION = "validacion"
    NEGOCIO = "negocio"
    PERMISO = "permiso"


class Codigo:
    """Códigos estables de error; las herramientas agregan los suyos."""

    FALLA_TRANSITORIA = "FALLA_TRANSITORIA"
    NO_ENCONTRADO = "NO_ENCONTRADO"
    PARAMETRO_INVALIDO = "PARAMETRO_INVALIDO"


def exito(datos) -> dict:
    """Respuesta exitosa. Una búsqueda sin resultados es ``exito([])``, no un error."""
    return {"ok": True, "datos": datos}


def error(tipo: TipoError, codigo: str, mensaje: str) -> dict:
    """Respuesta de error con el contrato completo."""
    if not isinstance(tipo, TipoError):
        raise TypeError(f"tipo de error fuera del contrato: {tipo!r}")
    return {
        "ok": False,
        "error": {
            "tipo": tipo.value,
            "codigo": codigo,
            "mensaje": mensaje,
            "reintentable": tipo is TipoError.TRANSITORIO,
        },
    }
