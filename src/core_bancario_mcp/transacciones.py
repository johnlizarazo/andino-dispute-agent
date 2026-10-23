"""Herramientas de transacciones del core: ``consultar_transacciones`` e ``iniciar_disputa``.

Las fechas se calculan siempre respecto de ``repositorio.hoy`` (inyectable), y el monto de una
disputa sale de los datos del core, nunca de un argumento (regla 2). Las funciones son puras
sobre un ``Contexto``; ``registrar`` las publica en el servidor.
"""

import re
from datetime import date, timedelta

from mcp.server.fastmcp import FastMCP

from core_bancario_mcp.contexto import Contexto
from core_bancario_mcp.errores import Codigo, TipoError, error, exito
from core_bancario_mcp.fallas import con_fallas
from core_bancario_mcp.identificacion import Texto
from core_bancario_mcp.repositorio import PATRON_CUATRO_DIGITOS

# date.fromisoformat también acepta "20261023" o semanas ISO; se exige año-mes-día.
PATRON_FECHA = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
DIAS_POR_OMISION = 30
DIAS_MAXIMOS_RANGO = 365
LARGO_MAXIMO_MOTIVO = 500

DESCRIPCION_CONSULTAR = (
    "Lista los cobros de una tarjeta del cliente, identificada por cliente_id y ultimos4, "
    "en un rango de fechas AAAA-MM-DD (fecha_desde y fecha_hasta; por omisión, los "
    "últimos 30 días). Requiere la identidad verificada del titular de la tarjeta. Úsala "
    "para ubicar con el cliente el cobro que no reconoce antes de disputarlo. Un cobro con "
    "caso_disputa ya tiene una disputa abierta. Una lista vacía significa que no hay "
    "cobros en el rango; no es un error."
)
DESCRIPCION_DISPUTAR = (
    "Abre una disputa sobre un cobro que el cliente no reconoce (transaccion_id de "
    "consultar_transacciones y el motivo) y devuelve el número de caso. Requiere la "
    "identidad verificada del titular. El monto lo toma el core de sus datos; no se envía. "
    "Si responde FUERA_DE_POLITICA o REQUIERE_ANALISTA, no reintentes: el caso debe "
    "escalarse a un analista. Si responde DISPUTA_EXISTENTE, informa el caso que ya existe."
)


def _invalido(mensaje: str) -> dict:
    return error(TipoError.VALIDACION, Codigo.PARAMETRO_INVALIDO, mensaje)


def tarjeta_no_encontrada(ultimos4: str) -> dict:
    """Mismo error si el cliente no existe o la tarjeta es de otra persona."""
    return error(
        TipoError.VALIDACION,
        Codigo.NO_ENCONTRADO,
        f"No hay una tarjeta terminada en {ultimos4} para ese cliente.",
    )


def _fecha(campo: str, valor: str) -> date:
    """Fecha AAAA-MM-DD; ``ValueError`` con un mensaje para el agente si no lo es."""
    if not PATRON_FECHA.fullmatch(valor):
        raise ValueError(f"{campo} debe tener el formato AAAA-MM-DD")
    try:
        return date.fromisoformat(valor)
    except ValueError as e:
        raise ValueError(f"{campo} no es una fecha válida") from e


def consultar_transacciones(
    contexto: Contexto,
    cliente_id=None,
    ultimos4=None,
    fecha_desde=None,
    fecha_hasta=None,
) -> dict:
    argumentos = {
        "cliente_id": cliente_id,
        "ultimos4": ultimos4,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
    }
    for campo, valor in argumentos.items():
        if valor is not None and not isinstance(valor, str):
            return _invalido(f"{campo} debe ser texto")
    cliente_id = (cliente_id or "").strip()
    ultimos4 = (ultimos4 or "").strip()
    # Una fecha vacía o de solo espacios se trata como omitida.
    fecha_desde = (fecha_desde or "").strip()
    fecha_hasta = (fecha_hasta or "").strip()
    if not cliente_id:
        return _invalido("cliente_id es obligatorio")
    if not PATRON_CUATRO_DIGITOS.fullmatch(ultimos4):
        return _invalido("ultimos4 debe tener exactamente 4 dígitos")

    repositorio = contexto.repositorio
    hoy = repositorio.hoy
    try:
        hasta = _fecha("fecha_hasta", fecha_hasta) if fecha_hasta else hoy
        desde = (
            _fecha("fecha_desde", fecha_desde)
            if fecha_desde
            else hasta - timedelta(days=DIAS_POR_OMISION - 1)
        )
    except ValueError as e:
        return _invalido(str(e))
    if desde > hasta:
        return _invalido("fecha_desde no puede ser posterior a fecha_hasta")
    if hasta > hoy:
        return _invalido(
            f"fecha_hasta no puede ser posterior a hoy ({hoy.isoformat()})"
        )
    if (hasta - desde).days > DIAS_MAXIMOS_RANGO:
        return _invalido(f"el rango no puede superar {DIAS_MAXIMOS_RANGO} días")

    tarjetas = {t.id for t in repositorio.tarjetas_de(cliente_id, ultimos4)}
    if not tarjetas:
        return tarjeta_no_encontrada(ultimos4)
    cobros = [
        t
        for t in repositorio.transacciones.values()
        if t.tarjeta_id in tarjetas and desde <= t.fecha <= hasta
    ]
    cobros.sort(key=lambda t: t.id)
    cobros.sort(key=lambda t: t.fecha, reverse=True)
    return exito(
        [
            {
                "transaccion_id": t.id,
                "fecha": t.fecha.isoformat(),
                "monto": t.monto,
                "comercio": t.comercio,
                "pais": t.pais,
                "caso_disputa": (
                    caso.id if (caso := contexto.disputas.caso_de(t.id)) else None
                ),
            }
            for t in cobros
        ]
    )


def iniciar_disputa(contexto: Contexto, transaccion_id=None, motivo=None) -> dict:
    for campo, valor in (("transaccion_id", transaccion_id), ("motivo", motivo)):
        if not isinstance(valor, str) or not valor.strip():
            return _invalido(f"{campo} es obligatorio y debe ser texto")
    transaccion_id, motivo = transaccion_id.strip(), motivo.strip()
    if len(motivo) > LARGO_MAXIMO_MOTIVO:
        return _invalido(f"motivo no puede superar {LARGO_MAXIMO_MOTIVO} caracteres")

    transaccion = contexto.repositorio.obtener_transaccion(transaccion_id)
    if transaccion is None:
        return error(
            TipoError.VALIDACION,
            Codigo.NO_ENCONTRADO,
            f"No existe la transacción {transaccion_id}. "
            "Ubícala antes con consultar_transacciones.",
        )
    existente = contexto.disputas.caso_de(transaccion.id)
    if existente is not None:
        return error(
            TipoError.NEGOCIO,
            Codigo.DISPUTA_EXISTENTE,
            f"La transacción ya tiene la disputa {existente.id} abierta. "
            "Informa ese caso al cliente.",
        )

    # La política decide primero si el caso es disputable; después, el umbral (regla 2).
    repositorio = contexto.repositorio
    politica = repositorio.politica
    if not politica.cubre(transaccion, repositorio.hoy):
        antiguedad = (repositorio.hoy - transaccion.fecha).days
        limite = politica.limite_dias(transaccion)
        origen = "nacionales" if transaccion.pais == "CO" else "en el exterior"
        return error(
            TipoError.NEGOCIO,
            Codigo.FUERA_DE_POLITICA,
            f"El cobro tiene {antiguedad} días y la política cubre cobros {origen} "
            f"hasta {limite} días. No reintentes: escala el caso a un analista.",
        )
    if politica.requiere_analista(transaccion.monto):
        umbral = f"{politica.umbral_disputa_automatica:,}".replace(",", ".")
        return error(
            TipoError.NEGOCIO,
            Codigo.REQUIERE_ANALISTA,
            f"El monto supera el umbral de disputa automática (${umbral}). "
            "No reintentes: escala el caso a un analista.",
        )

    caso = contexto.disputas.abrir(transaccion, motivo)
    return exito(
        {
            "caso_id": caso.id,
            "transaccion_id": caso.transaccion_id,
            "monto": caso.monto,
            "estado": caso.estado,
        }
    )


def registrar(servidor: FastMCP, contexto: Contexto) -> None:
    """Publica las herramientas de transacciones sobre ``contexto``."""

    @servidor.tool(name="consultar_transacciones", description=DESCRIPCION_CONSULTAR)
    @con_fallas(contexto.inyector, "consultar_transacciones")
    def _consultar(
        cliente_id: Texto = None,
        ultimos4: Texto = None,
        fecha_desde: Texto = None,
        fecha_hasta: Texto = None,
    ) -> dict:
        return consultar_transacciones(
            contexto, cliente_id, ultimos4, fecha_desde, fecha_hasta
        )

    @servidor.tool(name="iniciar_disputa", description=DESCRIPCION_DISPUTAR)
    @con_fallas(contexto.inyector, "iniciar_disputa")
    def _disputar(transaccion_id: Texto = None, motivo: Texto = None) -> dict:
        return iniciar_disputa(contexto, transaccion_id, motivo)
