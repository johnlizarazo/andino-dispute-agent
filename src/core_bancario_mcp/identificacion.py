"""Herramientas de identificación del core: ``buscar_cliente`` y ``verificar_identidad``.

Buscar no verifica identidad: devuelve todas las coincidencias (solo id y nombre) y nunca
elige entre varias. Las funciones son puras sobre un ``Contexto``; ``registrar`` las publica
en el servidor con sus descripciones y la inyección de fallas.
"""

import hmac
import re
import unicodedata
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import WithJsonSchema

from core_bancario_mcp.contexto import Contexto
from core_bancario_mcp.errores import Codigo, TipoError, error, exito
from core_bancario_mcp.fallas import con_fallas
from core_bancario_mcp.repositorio import PATRON_CUATRO_DIGITOS, PATRON_DOCUMENTO

LARGO_MAXIMO_NOMBRE = 100

# El esquema publicado dice "texto" (guía al modelo), pero cualquier valor llega a la
# herramienta: así un número o una lista se responden con el contrato y no con un error de
# validación de FastMCP fuera de él.
Texto = Annotated[object, WithJsonSchema({"type": "string"})]

DESCRIPCION_BUSCAR = (
    "Busca clientes por UN solo criterio: documento (formato CC-FIC-NNNN), nombre o "
    "ultimos4 (los últimos 4 dígitos de una tarjeta). Devuelve todas las coincidencias, "
    "solo con cliente_id y nombre. Buscar NO verifica identidad: después de una única "
    "coincidencia usa verificar_identidad. Si hay varias coincidencias, NO elijas: pide "
    "al cliente otro identificador (su documento o los últimos 4 de su tarjeta) y busca "
    "de nuevo. Una lista vacía significa que no hay coincidencias; no es un error."
)
DESCRIPCION_VERIFICAR = (
    "Confirma la identidad de un cliente con su dato de verificación, un dato que solo "
    "el cliente conoce. Úsala solo después de que buscar_cliente devolvió una única "
    "coincidencia, con su cliente_id. Si el dato no coincide, no reintentes con un dato "
    "inventado: pide al cliente que lo confirme. Tras 3 fallos el core bloquea la "
    "verificación de ese cliente y debes escalar a un analista."
)


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


def verificar_identidad(
    contexto: Contexto, cliente_id=None, dato_verificacion=None
) -> dict:
    for campo, valor in (
        ("cliente_id", cliente_id),
        ("dato_verificacion", dato_verificacion),
    ):
        if not isinstance(valor, str) or not valor.strip():
            return _invalido(f"{campo} es obligatorio y debe ser texto")
    cliente = contexto.repositorio.clientes.get(cliente_id)
    if cliente is None:
        return error(
            TipoError.VALIDACION,
            Codigo.NO_ENCONTRADO,
            f"No existe el cliente {cliente_id}. Búscalo antes con buscar_cliente.",
        )
    intentos = contexto.intentos
    if intentos.agotados(cliente.id):
        return error(
            TipoError.NEGOCIO,
            Codigo.INTENTOS_AGOTADOS,
            "La verificación de este cliente está bloqueada por intentos fallidos. "
            "No sigas intentando: escala el caso a un analista.",
        )
    if hmac.compare_digest(
        dato_verificacion.encode(), cliente.dato_verificacion.encode()
    ):
        intentos.reiniciar(cliente.id)
        return exito({"cliente_id": cliente.id, "verificado": True})
    intentos.registrar_fallo(cliente.id)
    return error(
        TipoError.PERMISO,
        Codigo.VERIFICACION_FALLIDA,
        "El dato de verificación no coincide. Pide al cliente que lo confirme; "
        "no lo reintentes con un dato inventado.",
    )


def registrar(servidor: FastMCP, contexto: Contexto) -> None:
    """Publica las herramientas de identificación sobre ``contexto``."""

    @servidor.tool(name="buscar_cliente", description=DESCRIPCION_BUSCAR)
    @con_fallas(contexto.inyector, "buscar_cliente")
    def _buscar(
        documento: Texto = None, nombre: Texto = None, ultimos4: Texto = None
    ) -> dict:
        return buscar_cliente(contexto, documento, nombre, ultimos4)

    @servidor.tool(name="verificar_identidad", description=DESCRIPCION_VERIFICAR)
    @con_fallas(contexto.inyector, "verificar_identidad")
    def _verificar(cliente_id: Texto = None, dato_verificacion: Texto = None) -> dict:
        return verificar_identidad(contexto, cliente_id, dato_verificacion)
