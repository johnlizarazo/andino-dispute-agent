"""Eventos visibles de un turno: lo que cambió o se impidió, en lenguaje de negocio (#12).

``LectorEventos`` empareja cada llamada a herramienta (``ToolUseBlock``) con su resultado
(``ToolResultBlock``) por ``tool_use_id``; lee la respuesta del core con el contrato
``ok``/``datos``/``error`` y reconoce las llamadas negadas por los controles en su registro de
negaciones. Nunca usa el texto que redacta el modelo: un evento refleja lo que ocurrió, y no
hay éxito sin ``ok: true`` del core (contrato en ``specs/012-interfaz-chat/contracts``).
"""

from dataclasses import dataclass

from claude_agent_sdk import (
    AssistantMessage,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from agente_disputas.analista import HERRAMIENTA_DELEGAR, pesos
from agente_disputas.controles import (
    BLOQUEAR,
    BUSCAR,
    CONSULTAR,
    DISPUTAR,
    ESCALAR,
    VERIFICAR,
    EstadoSesion,
    leer_respuesta,
)

EXITO = "exito"
NEGADO = "negado"
FALLA = "falla"
PREFIJOS = {EXITO: "✅", NEGADO: "⛔", FALLA: "⚠️"}

# Task es el nombre anterior de la delegación (mismo criterio que los controles).
DELEGAR = (HERRAMIENTA_DELEGAR, "Task")
OPERACIONES = {
    BUSCAR: "Búsqueda del cliente",
    VERIFICAR: "Verificación de identidad",
    CONSULTAR: "Consulta de transacciones",
    DISPUTAR: "Disputa",
    BLOQUEAR: "Bloqueo de tarjeta",
    ESCALAR: "Escalamiento",
    **dict.fromkeys(DELEGAR, "Análisis de transacciones"),
}
# Solo cambian algo, o explican por qué no: las lecturas exitosas no son eventos.
CON_EVENTO = (VERIFICAR, DISPUTAR, BLOQUEAR, ESCALAR)
MOTIVOS = {
    "persona_solicitada": "el cliente pidió hablar con una persona",
    "umbral": "el monto supera el umbral de disputa automática",
    "fuera_de_politica": "el caso está fuera de la política del banco",
    "intentos_agotados": "se agotaron los intentos de verificación",
    "otra": "otro motivo",
}
RAZONES = {
    "SIN_IDENTIDAD": "la identidad del cliente no está verificada",
    "CLIENTE_DISTINTO": "el producto no es del cliente verificado",
    "TRANSACCION_NO_CONFIRMADA": (
        "no se pudo confirmar que la transacción sea del cliente verificado"
    ),
    "REQUIERE_ANALISTA": (
        "el monto supera el umbral de disputa automática y requiere un analista"
    ),
    **dict.fromkeys(
        (
            "CONTEXTO_INCOMPLETO",
            "SUBAGENTE_NO_PERMITIDO",
            "SEGUNDO_PLANO_NO_PERMITIDO",
        ),
        "la solicitud de análisis no cumplió las condiciones",
    ),
}
RAZON_DESCONOCIDA = "no se pudo confirmar la operación"
VERIFICACION_FALLIDA = {
    "VERIFICACION_FALLIDA": "el dato de verificación no coincide",
    "INTENTOS_AGOTADOS": "se agotaron los intentos de verificación",
}
RECHAZOS_DEL_CORE = {
    "FUERA_DE_POLITICA": "Disputa fuera de la política del banco",
    "REQUIERE_ANALISTA": "Disputa por encima del umbral",
}


@dataclass(frozen=True)
class Evento:
    tipo: str
    resultado: str
    titulo: str
    detalle: str = ""


def formatear_evento(evento: Evento) -> str:
    """Prefijo según el resultado y título; el detalle, si hay, en la línea siguiente."""
    linea = f"{PREFIJOS[evento.resultado]} **{evento.titulo}**"
    return f"{linea}\n{evento.detalle}" if evento.detalle else linea


def _falla(herramienta: str, detalle: str) -> Evento:
    titulo = f"No se pudo completar: {OPERACIONES.get(herramienta, 'la operación')}"
    return Evento("falla", FALLA, titulo, detalle)


def _sin_confirmar(herramienta: str) -> Evento:
    return _falla(herramienta, "No se pudo confirmar el resultado; no se da por hecha.")


def _exito_del_core(herramienta: str, datos) -> Evento | None:
    if herramienta == VERIFICAR:
        if datos.get("verificado") is not True:
            return Evento("identidad", FALLA, "No se pudo verificar la identidad")
        return Evento(
            "identidad", EXITO, "Identidad verificada", f"Cliente {datos['cliente_id']}"
        )
    if herramienta == BLOQUEAR:
        detalle = f"•••• {datos['ultimos4']}"
        if datos.get("ya_estaba_bloqueada") is True:
            detalle += " (ya estaba bloqueada)"
        return Evento("bloqueo", EXITO, "Tarjeta bloqueada", detalle)
    if herramienta == DISPUTAR:
        detalle = (
            f"Caso {datos['caso_id']} · transacción {datos['transaccion_id']} · "
            f"{pesos(datos['monto'])}"
        )
        return Evento("disputa", EXITO, "Disputa iniciada", detalle)
    if herramienta == ESCALAR:
        motivo = MOTIVOS.get(datos.get("causa"), "motivo no indicado")
        detalle = f"Caso {datos['escalamiento_id']} · motivo: {motivo}"
        return Evento("escalamiento", EXITO, "Caso escalado a un analista", detalle)
    return None


def _error_del_core(herramienta: str, argumentos: dict, error: dict) -> Evento:
    codigo, tipo = error.get("codigo"), error.get("tipo")
    if tipo == "transitorio":
        return _falla(herramienta, "Hubo un error temporal del sistema; no se realizó.")
    if herramienta == VERIFICAR:
        motivo = VERIFICACION_FALLIDA.get(codigo, RAZON_DESCONOCIDA)
        return Evento(
            "identidad", FALLA, "No se pudo verificar la identidad", motivo.capitalize()
        )
    if herramienta == DISPUTAR and codigo in RECHAZOS_DEL_CORE:
        transaccion = argumentos.get("transaccion_id", "indicada")
        detalle = f"Transacción {transaccion}: requiere un analista."
        return Evento("rechazo_politica", NEGADO, RECHAZOS_DEL_CORE[codigo], detalle)
    return _falla(
        herramienta, "El core no la aceptó por datos inválidos o no hallados."
    )


def _del_core(herramienta: str, argumentos: dict, contenido) -> Evento | None:
    respuesta = leer_respuesta(contenido)
    if respuesta is None or respuesta["ok"] not in (True, False):
        return _sin_confirmar(herramienta) if herramienta in CON_EVENTO else None
    try:
        if respuesta["ok"] is True:
            datos = respuesta["datos"]
            if herramienta not in CON_EVENTO:
                return None
            return _exito_del_core(herramienta, datos)
        return _error_del_core(herramienta, argumentos, respuesta["error"])
    except KeyError, TypeError, AttributeError, ValueError:
        # Una respuesta incompleta nunca se presenta como éxito.
        return _sin_confirmar(herramienta)


class LectorEventos:
    """Eventos de un turno a partir de sus mensajes, en el orden de los resultados."""

    def __init__(self, estado: EstadoSesion):
        self.estado = estado
        # Las negaciones anteriores son de otros turnos.
        self._desde = len(estado.negaciones)
        self._pendientes: dict[str, ToolUseBlock] = {}
        self._cerradas: set[str] = set()

    def _negacion(self, uso: str):
        for negacion in self.estado.negaciones[self._desde :]:
            if negacion.tool_use_id == uso:
                return negacion
        return None

    def _evento_negado(self, llamada: ToolUseBlock, codigo: str) -> Evento:
        operacion = OPERACIONES.get(llamada.name, "Operación")
        razon = RAZONES.get(codigo, RAZON_DESCONOCIDA)
        return Evento(
            "negacion",
            NEGADO,
            "Operación negada por un control del banco",
            f"{operacion}: {razon}",
        )

    def _cerrar_llamada(self, uso: str, resultado: ToolResultBlock | None):
        llamada = self._pendientes.pop(uso)
        self._cerradas.add(uso)
        negacion = self._negacion(uso)
        if negacion is not None:
            return self._evento_negado(llamada, negacion.codigo)
        if resultado is None:
            return _sin_confirmar(llamada.name)
        if llamada.name in DELEGAR:
            # El resultado es el texto del subagente, no el contrato del core (ajuste I1).
            if resultado.is_error is True:
                return _falla(llamada.name, "")
            return Evento("analisis", EXITO, "Análisis de transacciones realizado")
        argumentos = llamada.input if isinstance(llamada.input, dict) else {}
        return _del_core(llamada.name, argumentos, resultado.content)

    def leer(self, mensaje) -> list[Evento]:
        if not isinstance(mensaje, AssistantMessage | UserMessage):
            return []
        if not isinstance(mensaje.content, list):
            return []
        eventos = []
        for bloque in mensaje.content:
            if isinstance(bloque, ToolUseBlock) and bloque.id not in self._cerradas:
                self._pendientes[bloque.id] = bloque
            elif (
                isinstance(bloque, ToolResultBlock)
                and bloque.tool_use_id in self._pendientes
            ):
                evento = self._cerrar_llamada(bloque.tool_use_id, bloque)
                if evento is not None:
                    eventos.append(evento)
        return eventos

    def cerrar(self) -> list[Evento]:
        """Al terminar el turno, las llamadas sin resultado: negadas o sin confirmar."""
        return [self._cerrar_llamada(uso, None) for uso in list(self._pendientes)]
