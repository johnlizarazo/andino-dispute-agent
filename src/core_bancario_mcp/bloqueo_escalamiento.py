"""Herramientas de bloqueo y escalamiento: ``bloquear_tarjeta`` y ``escalar_a_analista``.

El bloqueo es inmediato y no tiene paso de aprobación (regla 3). El escalamiento no exige
identidad verificada, así que su respuesta no expone datos de productos: el resumen completo
queda registrado para el analista. Las funciones son puras sobre un ``Contexto``.
"""

import json

from mcp.server.fastmcp import FastMCP

from core_bancario_mcp.contexto import Contexto, DetalleTransaccion
from core_bancario_mcp.errores import Codigo, TipoError, error, exito
from core_bancario_mcp.fallas import con_fallas
from core_bancario_mcp.identificacion import ListaTexto, Texto
from core_bancario_mcp.repositorio import PATRON_CUATRO_DIGITOS
from core_bancario_mcp.transacciones import tarjeta_no_encontrada

LARGO_MAXIMO_MOTIVO = 500
LARGO_MAXIMO_ACCIONES = 1000
LARGO_MAXIMO_RECOMENDACION = 500
CAUSAS = (
    "persona_solicitada",
    "umbral",
    "fuera_de_politica",
    "intentos_agotados",
    "otra",
)
CAUSAS_SIN_CLIENTE = {
    "persona_solicitada"
}  # regla 4: se escala aunque no esté identificado
CAUSAS_CON_TRANSACCIONES = {"umbral", "fuera_de_politica"}

DESCRIPCION_BLOQUEAR = (
    "Bloquea de inmediato una tarjeta del cliente, identificada por cliente_id y ultimos4, "
    "por sospecha de fraude, con el motivo. Requiere la identidad verificada del titular. "
    "No requiere ni espera la aprobación de un analista: el bloqueo ocurre en el mismo "
    "llamado. Si la tarjeta ya estaba bloqueada responde ya_estaba_bloqueada; no es un error."
)
DESCRIPCION_ESCALAR = (
    "Escala el caso a un analista humano con un resumen estructurado: causa, cliente_id, "
    "transacciones (solo sus ids), acciones_realizadas y accion_recomendada. No requiere "
    "identidad verificada. Si el cliente pide hablar con una persona, escala de inmediato "
    "con causa persona_solicitada, aunque no esté identificado. Úsala también cuando el "
    "core responde REQUIERE_ANALISTA (causa umbral), FUERA_DE_POLITICA (causa "
    "fuera_de_politica) o INTENTOS_AGOTADOS (causa intentos_agotados); para lo demás, causa "
    "otra. El core completa los montos y guarda el resumen para el analista; responde el "
    "número de escalamiento para informarlo al cliente."
)


def _invalido(mensaje: str) -> dict:
    return error(TipoError.VALIDACION, Codigo.PARAMETRO_INVALIDO, mensaje)


def bloquear_tarjeta(
    contexto: Contexto, cliente_id=None, ultimos4=None, motivo=None
) -> dict:
    for campo, valor in (
        ("cliente_id", cliente_id),
        ("ultimos4", ultimos4),
        ("motivo", motivo),
    ):
        if not isinstance(valor, str) or not valor.strip():
            return _invalido(f"{campo} es obligatorio y debe ser texto")
    cliente_id, ultimos4, motivo = cliente_id.strip(), ultimos4.strip(), motivo.strip()
    if not PATRON_CUATRO_DIGITOS.fullmatch(ultimos4):
        return _invalido("ultimos4 debe tener exactamente 4 dígitos")
    if len(motivo) > LARGO_MAXIMO_MOTIVO:
        return _invalido(f"motivo no puede superar {LARGO_MAXIMO_MOTIVO} caracteres")

    tarjetas = contexto.repositorio.tarjetas_de(cliente_id, ultimos4)
    if not tarjetas:
        return tarjeta_no_encontrada(ultimos4)
    ya_estaban = [contexto.bloqueos.bloquear(t, motivo) for t in tarjetas]
    return exito(
        {
            "ultimos4": ultimos4,
            "estado": "bloqueada",
            "ya_estaba_bloqueada": all(ya_estaban),
        }
    )


def _lista_de_ids(valor) -> list[str] | None:
    """Ids recortados y sin repetir; acepta una lista o un texto con una lista JSON.

    Devuelve ``None`` si el valor no es una lista de textos (algunos clientes MCP envían los
    arreglos como texto JSON; cualquier otra forma es un parámetro inválido).
    """
    if valor is None:
        return []
    if isinstance(valor, str):
        try:
            valor = json.loads(valor)
        except ValueError:
            return None
    if not isinstance(valor, list) or not all(isinstance(v, str) for v in valor):
        return None
    return list(dict.fromkeys(v.strip() for v in valor if v.strip()))


def escalar_a_analista(
    contexto: Contexto,
    causa=None,
    cliente_id=None,
    transacciones=None,
    acciones_realizadas=None,
    accion_recomendada=None,
) -> dict:
    textos = {
        "causa": causa,
        "cliente_id": cliente_id,
        "acciones_realizadas": acciones_realizadas,
        "accion_recomendada": accion_recomendada,
    }
    for campo, valor in textos.items():
        if valor is not None and not isinstance(valor, str):
            return _invalido(f"{campo} debe ser texto")
    ids = _lista_de_ids(transacciones)
    if ids is None:
        return _invalido("transacciones debe ser una lista de ids de transacción")
    causa, cliente_id, acciones, recomendacion = (
        (v or "").strip() for v in textos.values()
    )

    faltan = [
        campo
        for campo, valor in (
            ("causa", causa),
            ("acciones_realizadas", acciones),
            ("accion_recomendada", recomendacion),
        )
        if not valor
    ]
    if faltan:
        return _invalido(f"Faltan campos obligatorios del resumen: {', '.join(faltan)}")
    if causa not in CAUSAS:
        return _invalido(f"causa debe ser una de: {', '.join(CAUSAS)}")
    if len(acciones) > LARGO_MAXIMO_ACCIONES:
        return _invalido(
            f"acciones_realizadas no puede superar {LARGO_MAXIMO_ACCIONES} caracteres"
        )
    if len(recomendacion) > LARGO_MAXIMO_RECOMENDACION:
        return _invalido(
            f"accion_recomendada no puede superar {LARGO_MAXIMO_RECOMENDACION} caracteres"
        )

    repositorio = contexto.repositorio
    cliente = None
    if cliente_id:
        cliente = repositorio.clientes.get(cliente_id)
        if cliente is None:
            return error(
                TipoError.VALIDACION,
                Codigo.NO_ENCONTRADO,
                f"No existe el cliente {cliente_id}.",
            )
    elif causa not in CAUSAS_SIN_CLIENTE:
        return _invalido(f"cliente_id es obligatorio con la causa {causa}")

    if causa in CAUSAS_CON_TRANSACCIONES and not ids:
        return _invalido(f"transacciones es obligatoria con la causa {causa}")
    detalles = []
    for transaccion_id in ids:
        transaccion = repositorio.obtener_transaccion(transaccion_id)
        if transaccion is None:
            return error(
                TipoError.VALIDACION,
                Codigo.NO_ENCONTRADO,
                f"No existe la transacción {transaccion_id}.",
            )
        if cliente is not None and transaccion.cliente_id != cliente.id:
            return _invalido(f"La transacción {transaccion_id} no es de ese cliente")
        caso = contexto.disputas.caso_de(transaccion.id)
        detalles.append(
            DetalleTransaccion(
                transaccion_id=transaccion.id,
                fecha=transaccion.fecha.isoformat(),
                monto=transaccion.monto,
                comercio=transaccion.comercio,
                caso_disputa=caso.id if caso else None,
            )
        )

    escalamiento = contexto.escalamientos.registrar(
        causa,
        cliente.id if cliente else None,
        cliente.nombre if cliente else None,
        tuple(detalles),
        acciones,
        recomendacion,
    )
    # Escalar no exige identidad verificada: la respuesta no lleva datos de productos.
    return exito(
        {
            "escalamiento_id": escalamiento.id,
            "causa": escalamiento.causa,
            "estado": escalamiento.estado,
            "cantidad_transacciones": len(escalamiento.transacciones),
        }
    )


def registrar(servidor: FastMCP, contexto: Contexto) -> None:
    """Publica las herramientas de bloqueo y escalamiento sobre ``contexto``."""

    @servidor.tool(name="bloquear_tarjeta", description=DESCRIPCION_BLOQUEAR)
    @con_fallas(contexto.inyector, "bloquear_tarjeta")
    def _bloquear(
        cliente_id: Texto = None, ultimos4: Texto = None, motivo: Texto = None
    ) -> dict:
        return bloquear_tarjeta(contexto, cliente_id, ultimos4, motivo)

    @servidor.tool(name="escalar_a_analista", description=DESCRIPCION_ESCALAR)
    @con_fallas(contexto.inyector, "escalar_a_analista")
    def _escalar(
        causa: Texto = None,
        cliente_id: Texto = None,
        transacciones: ListaTexto = None,
        acciones_realizadas: Texto = None,
        accion_recomendada: Texto = None,
    ) -> dict:
        return escalar_a_analista(
            contexto,
            causa,
            cliente_id,
            transacciones,
            acciones_realizadas,
            accion_recomendada,
        )
