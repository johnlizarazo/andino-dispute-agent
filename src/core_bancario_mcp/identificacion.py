"""Herramientas de identificación del core: ``buscar_cliente`` y ``verificar_identidad``.

Buscar no verifica identidad: devuelve todas las coincidencias (solo id y nombre) y nunca
elige entre varias. Las funciones son puras sobre un ``Contexto``; ``registrar`` las publica
en el servidor con sus descripciones y la inyección de fallas.
"""

import re
import unicodedata

from core_bancario_mcp.contexto import Contexto
from core_bancario_mcp.errores import Codigo, TipoError, error, exito
from core_bancario_mcp.repositorio import PATRON_CUATRO_DIGITOS, PATRON_DOCUMENTO

LARGO_MAXIMO_NOMBRE = 100


def _invalido(mensaje: str) -> dict:
    return error(TipoError.VALIDACION, Codigo.PARAMETRO_INVALIDO, mensaje)


def _palabras(texto: str) -> list[str]:
    """Palabras sin tildes ni mayúsculas: "Pérez," y "PEREZ" quedan como "perez"."""
    sin_marcas = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return re.findall(r"\w+", sin_marcas.casefold())


def buscar_cliente(
    contexto: Contexto, documento=None, nombre=None, ultimos4=None
) -> dict:
    criterios = {"documento": documento, "nombre": nombre, "ultimos4": ultimos4}
    for campo, valor in criterios.items():
        if valor is not None and not isinstance(valor, str):
            return _invalido(f"{campo} debe ser texto")
    dados = {c: v.strip() for c, v in criterios.items() if v is not None and v.strip()}
    if len(dados) != 1:
        return _invalido(
            "Usa exactamente un criterio: documento (CC-FIC-NNNN), nombre o ultimos4 "
            "(los últimos 4 dígitos de la tarjeta)."
        )
    ((campo, valor),) = dados.items()
    clientes = contexto.repositorio.clientes

    if campo == "documento":
        if not PATRON_DOCUMENTO.fullmatch(valor):
            return _invalido("documento debe tener el formato CC-FIC-NNNN")
        encontrados = [c for c in clientes.values() if c.documento == valor]
    elif campo == "ultimos4":
        if not PATRON_CUATRO_DIGITOS.fullmatch(valor):
            return _invalido("ultimos4 debe tener exactamente 4 dígitos")
        titulares = {
            t.cliente_id
            for t in contexto.repositorio.tarjetas.values()
            if t.ultimos4 == valor
        }
        encontrados = [clientes[cliente_id] for cliente_id in titulares]
    else:
        buscadas = _palabras(valor)
        if len("".join(buscadas)) < 2 or len(valor) > LARGO_MAXIMO_NOMBRE:
            return _invalido(
                f"nombre debe tener al menos 2 letras y hasta {LARGO_MAXIMO_NOMBRE} "
                "caracteres"
            )
        encontrados = [
            c for c in clientes.values() if set(buscadas) <= set(_palabras(c.nombre))
        ]

    return exito(
        [
            {"cliente_id": c.id, "nombre": c.nombre}
            for c in sorted(encontrados, key=lambda c: c.id)
        ]
    )
