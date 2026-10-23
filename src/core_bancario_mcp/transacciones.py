"""Herramientas de transacciones del core: ``consultar_transacciones`` e ``iniciar_disputa``.

Las fechas se calculan siempre respecto de ``repositorio.hoy`` (inyectable), y el monto de una
disputa sale de los datos del core, nunca de un argumento (regla 2). Las funciones son puras
sobre un ``Contexto``; ``registrar`` las publica en el servidor.
"""

import re
from datetime import date, timedelta

from core_bancario_mcp.contexto import Contexto
from core_bancario_mcp.errores import Codigo, TipoError, error, exito
from core_bancario_mcp.repositorio import PATRON_CUATRO_DIGITOS

# date.fromisoformat también acepta "20261023" o semanas ISO; se exige año-mes-día.
PATRON_FECHA = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
DIAS_POR_OMISION = 30
DIAS_MAXIMOS_RANGO = 365
LARGO_MAXIMO_MOTIVO = 500


def _invalido(mensaje: str) -> dict:
    return error(TipoError.VALIDACION, Codigo.PARAMETRO_INVALIDO, mensaje)


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
    if not cliente_id:
        return _invalido("cliente_id es obligatorio")
    if not PATRON_CUATRO_DIGITOS.fullmatch(ultimos4):
        return _invalido("ultimos4 debe tener exactamente 4 dígitos")

    repositorio = contexto.repositorio
    hoy = repositorio.hoy
    try:
        hasta = _fecha("fecha_hasta", fecha_hasta.strip()) if fecha_hasta else hoy
        desde = (
            _fecha("fecha_desde", fecha_desde.strip())
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
        # Mismo mensaje si el cliente no existe o la tarjeta es de otra persona.
        return error(
            TipoError.VALIDACION,
            Codigo.NO_ENCONTRADO,
            f"No hay una tarjeta terminada en {ultimos4} para ese cliente.",
        )
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

    caso = contexto.disputas.abrir(transaccion, motivo)
    return exito(
        {
            "caso_id": caso.id,
            "transaccion_id": caso.transaccion_id,
            "monto": caso.monto,
            "estado": caso.estado,
        }
    )
