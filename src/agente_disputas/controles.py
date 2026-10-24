"""Controles del agente: hooks del SDK que garantizan reglas del banco (principio II).

Reglas 1 y 2 (#9): un hook ``PostToolUse`` sobre ``verificar_identidad`` registra en el estado
de la conversación el cliente verificado; un hook ``PreToolUse`` sobre las herramientas que
operan sobre productos niega sin identidad verificada, sobre productos de otro cliente o con
una disputa por encima del umbral. El monto y el titular se leen de los datos del core por el
``transaccion_id``, nunca de otro argumento del modelo. Estos controles fallan cerrado: si no
pueden obtener el dato o algo falla, niegan. No leen el prompt de sistema.

Escalar tras una negación (#10): una disputa negada por umbral o rechazada por el core por
umbral o política queda como escalamiento pendiente; un hook ``Stop`` impide terminar el turno
mientras quede alguno, con un tope de ``MAXIMO_CIERRES_IMPEDIDOS``. Un escalamiento exitoso
con esa transacción y esa causa lo limpia, y cada mensaje nuevo del cliente vacía los
pendientes (el agente decide de nuevo con lo que diga el cliente).

Delegación (#11): un hook ``PreToolUse`` sobre la herramienta de delegación solo deja delegar
en ``analista-transacciones``, sin segundo plano, con cliente verificado y un bloque
``<contexto>`` completo para ese cliente. Las consultas del subagente pasan por los mismos
controles de las reglas 1 y 2 (llegan con ``agent_id``).
"""

import json
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass, field

from claude_agent_sdk import HookMatcher

from agente_disputas.analista import NOMBRE as NOMBRE_ANALISTA
from agente_disputas.analista import leer_contexto, pesos
from core_bancario_mcp.bloqueo_escalamiento import lista_de_ids
from core_bancario_mcp.fallas import VARIABLE as VARIABLE_FALLAS
from core_bancario_mcp.fallas import InyectorFallas
from core_bancario_mcp.repositorio import Politica, Repositorio, Transaccion

PREFIJO = "mcp__core-bancario__"
CONSULTAR = PREFIJO + "consultar_transacciones"
DISPUTAR = PREFIJO + "iniciar_disputa"
BLOQUEAR = PREFIJO + "bloquear_tarjeta"
VERIFICAR = PREFIJO + "verificar_identidad"
ESCALAR = PREFIJO + "escalar_a_analista"
SOBRE_PRODUCTOS = (CONSULTAR, DISPUTAR, BLOQUEAR)
# Operación de CORE_BANCARIO_FALLAS que hace fallar la consulta de datos del control.
OPERACION_FALLAS = "control_transaccion"
# Los controles son consultas en memoria; el tope solo evita esperar de más.
TIEMPO_MAXIMO_SEGUNDOS = 10
# Nombre con el que se registra una negación cuando la entrada no trae la herramienta.
HERRAMIENTA_DESCONOCIDA = "desconocida"
# Causas de un escalamiento pendiente: mismos valores que las de escalar_a_analista.
UMBRAL = "umbral"
FUERA_DE_POLITICA = "fuera_de_politica"
# Tope del hook Stop: no forzar un ciclo sin salida si el escalamiento sigue fallando.
MAXIMO_CIERRES_IMPEDIDOS = 2
# Códigos del core que obligan a escalar una disputa rechazada.
CAUSA_POR_CODIGO_DEL_CORE = {
    "REQUIERE_ANALISTA": UMBRAL,
    "FUERA_DE_POLITICA": FUERA_DE_POLITICA,
}

SIN_IDENTIDAD = "SIN_IDENTIDAD"
CLIENTE_DISTINTO = "CLIENTE_DISTINTO"
TRANSACCION_NO_CONFIRMADA = "TRANSACCION_NO_CONFIRMADA"
REQUIERE_ANALISTA = "REQUIERE_ANALISTA"
FALLA_CONTROL = "FALLA_CONTROL"
SUBAGENTE_NO_PERMITIDO = "SUBAGENTE_NO_PERMITIDO"
SEGUNDO_PLANO_NO_PERMITIDO = "SEGUNDO_PLANO_NO_PERMITIDO"
CONTEXTO_INCOMPLETO = "CONTEXTO_INCOMPLETO"
# Las razones nunca nombran a otro cliente ni dicen si una transacción existe.
RAZONES = {
    SUBAGENTE_NO_PERMITIDO: f"Solo puedes delegar en el subagente {NOMBRE_ANALISTA}.",
    SEGUNDO_PLANO_NO_PERMITIDO: (
        "Delega sin segundo plano: necesitas el resultado del análisis en este turno."
    ),
    SIN_IDENTIDAD: "Primero verifica la identidad del cliente con verificar_identidad.",
    CLIENTE_DISTINTO: (
        "Solo puedes operar sobre productos del cliente verificado en esta conversación."
    ),
    TRANSACCION_NO_CONFIRMADA: (
        "No se pudo confirmar que esa transacción pertenezca al cliente verificado."
    ),
    FALLA_CONTROL: "No se pudo confirmar la operación en este momento; no se realizó.",
}


class ConsultaFallidaError(Exception):
    """El control no pudo obtener los datos del core para decidir."""


def _sin_datos(_transaccion_id: str) -> Transaccion | None:
    raise ConsultaFallidaError("los datos del core no están disponibles")


@dataclass(frozen=True)
class Negacion:
    herramienta: str
    codigo: str


@dataclass
class EstadoSesion:
    """Lo que los controles recuerdan de una conversación; nace vacío con ella."""

    cliente_verificado: str | None = None
    negaciones: list[Negacion] = field(default_factory=list)
    # Transacción → causa (umbral o fuera de política) que falta escalar en este turno.
    pendientes: dict[str, str] = field(default_factory=dict)
    cierres_impedidos: int = 0


def _contrato(valor) -> dict | None:
    if isinstance(valor, dict) and "ok" in valor:
        return valor
    return None


def _desde_texto(texto) -> dict | None:
    if not isinstance(texto, str):
        return None
    try:
        return _contrato(json.loads(texto))
    except ValueError:
        return None


def _desde_bloques(bloques) -> dict | None:
    if not isinstance(bloques, list):
        return None
    for bloque in bloques:
        if isinstance(bloque, dict) and bloque.get("type") == "text":
            return _desde_texto(bloque.get("text"))
    return None


def leer_respuesta(tool_response) -> dict | None:
    """Respuesta del core según el contrato, o ``None`` si la forma no se reconoce.

    El SDK no fija la forma de ``tool_response`` para herramientas MCP; se aceptan el
    contrato tal cual, el contenido estructurado, los bloques de contenido y el texto JSON.
    """
    if isinstance(tool_response, dict):
        return (
            _contrato(tool_response)
            or _contrato(tool_response.get("structuredContent"))
            or _contrato(tool_response.get("structured_content"))
            or _desde_bloques(tool_response.get("content"))
        )
    return _desde_bloques(tool_response) or _desde_texto(tool_response)


def _texto(argumentos: dict, campo: str) -> str | None:
    """El argumento sin espacios, como lo lee el core, o ``None`` si no es texto."""
    valor = argumentos.get(campo)
    return valor.strip() if isinstance(valor, str) else None


@dataclass(frozen=True)
class Decision:
    autorizada: bool
    codigo: str | None = None
    razon: str | None = None
    # Transacción que queda pendiente de escalar (solo en la negación por umbral).
    pendiente: str | None = None


AUTORIZADA = Decision(True)


def negar(codigo: str) -> Decision:
    return Decision(False, codigo, RAZONES[codigo])


def negar_por_umbral(politica: Politica, transaccion_id: str) -> Decision:
    """La razón usa el umbral de la política, la misma fuente de la decisión."""
    umbral = pesos(politica.umbral_disputa_automatica)
    razon = (
        f"Esta disputa supera {umbral} y requiere un analista humano: escala el caso."
    )
    return Decision(False, REQUIERE_ANALISTA, razon, pendiente=transaccion_id)


class Controles:
    def __init__(
        self,
        buscar_transaccion: Callable[[str], Transaccion | None],
        politica: Politica | None,
        estado: EstadoSesion | None = None,
    ):
        self.buscar_transaccion = buscar_transaccion
        self.politica = politica
        self.estado = estado or EstadoSesion()

    @classmethod
    def desde_entorno(cls, entorno: Mapping[str, str]) -> Controles:
        """Controles con los datos del core; sin datos (todo niega) si no cargan."""
        try:
            repositorio = Repositorio()
            inyector = InyectorFallas(entorno.get(VARIABLE_FALLAS))
        except Exception:  # noqa: BLE001 - falla cerrada: sin datos, toda disputa niega
            return cls(_sin_datos, None)

        def buscar_transaccion(transaccion_id: str) -> Transaccion | None:
            if inyector.debe_fallar(OPERACION_FALLAS):
                raise ConsultaFallidaError("falla simulada en la consulta del control")
            return repositorio.obtener_transaccion(transaccion_id)

        return cls(buscar_transaccion, repositorio.politica)

    def hooks(self) -> dict[str, list[HookMatcher]]:
        """Hooks por nombre completo: cubren también las llamadas de un subagente."""
        return {
            "PreToolUse": [
                HookMatcher(
                    matcher="|".join(SOBRE_PRODUCTOS),
                    hooks=[self.antes_de_herramienta],
                    timeout=TIEMPO_MAXIMO_SEGUNDOS,
                ),
                # Agent es el nombre actual de la delegación; Task, el anterior.
                HookMatcher(
                    matcher="Agent|Task",
                    hooks=[self.antes_de_delegar],
                    timeout=TIEMPO_MAXIMO_SEGUNDOS,
                ),
            ],
            "PostToolUse": [
                HookMatcher(
                    matcher=VERIFICAR,
                    hooks=[self.despues_de_verificar],
                    timeout=TIEMPO_MAXIMO_SEGUNDOS,
                ),
                HookMatcher(
                    matcher=DISPUTAR,
                    hooks=[self.despues_de_disputar],
                    timeout=TIEMPO_MAXIMO_SEGUNDOS,
                ),
                HookMatcher(
                    matcher=ESCALAR,
                    hooks=[self.despues_de_escalar],
                    timeout=TIEMPO_MAXIMO_SEGUNDOS,
                ),
            ],
            "Stop": [
                HookMatcher(
                    hooks=[self.antes_de_terminar], timeout=TIEMPO_MAXIMO_SEGUNDOS
                )
            ],
            "UserPromptSubmit": [
                HookMatcher(
                    hooks=[self.al_recibir_mensaje], timeout=TIEMPO_MAXIMO_SEGUNDOS
                )
            ],
        }

    async def despues_de_verificar(self, entrada, tool_use_id, contexto) -> dict:
        """PostToolUse: solo un éxito explícito del core, para el cliente pedido, registra."""
        # Falla cerrada: cualquier error al leer la verificación no registra a nadie.
        with suppress(Exception):
            pedido = entrada["tool_input"]["cliente_id"].strip()
            respuesta = leer_respuesta(entrada["tool_response"])
            datos = respuesta["datos"] if respuesta and respuesta["ok"] is True else {}
            verificado = datos.get("cliente_id")
            if (
                datos.get("verificado") is True
                and isinstance(verificado, str)
                and verificado
                and verificado == pedido
            ):
                self.estado.cliente_verificado = verificado
        return {}

    async def antes_de_herramienta(self, entrada, tool_use_id, contexto) -> dict:
        """PreToolUse: autoriza solo si pasan todas las comprobaciones; si no, niega."""
        herramienta = HERRAMIENTA_DESCONOCIDA
        try:
            if isinstance(entrada.get("tool_name"), str):
                herramienta = entrada["tool_name"]
            decision = self.decidir(herramienta, entrada["tool_input"])
        except Exception:  # noqa: BLE001 - falla cerrada: cualquier error niega
            decision = negar(FALLA_CONTROL)
        return self._responder(herramienta, decision)

    async def antes_de_delegar(self, entrada, tool_use_id, contexto) -> dict:
        """PreToolUse sobre la delegación: subagente, identidad y contexto explícito."""
        herramienta = HERRAMIENTA_DESCONOCIDA
        try:
            if isinstance(entrada.get("tool_name"), str):
                herramienta = entrada["tool_name"]
            decision = self.decidir_delegacion(entrada["tool_input"])
        except Exception:  # noqa: BLE001 - falla cerrada: cualquier error niega
            decision = negar(FALLA_CONTROL)
        return self._responder(herramienta, decision)

    def decidir_delegacion(self, argumentos: dict) -> Decision:
        """Orden: subagente permitido, sin segundo plano, identidad, contexto, cliente."""
        if argumentos.get("subagent_type") != NOMBRE_ANALISTA:
            return negar(SUBAGENTE_NO_PERMITIDO)
        if argumentos.get("run_in_background") is True:
            return negar(SEGUNDO_PLANO_NO_PERMITIDO)
        if self.estado.cliente_verificado is None:
            return negar(SIN_IDENTIDAD)
        datos, invalidos = leer_contexto(argumentos.get("prompt"))
        if invalidos:
            # Solo nombres de campo: nunca valores, que podrían ser de otro cliente.
            razon = (
                "Falta o es inválido en el bloque <contexto>: "
                + ", ".join(invalidos)
                + "."
            )
            return Decision(False, CONTEXTO_INCOMPLETO, razon)
        if datos["cliente_id"] != self.estado.cliente_verificado:
            return negar(CLIENTE_DISTINTO)
        return AUTORIZADA

    def _responder(self, herramienta: str, decision: Decision) -> dict:
        """Salida del PreToolUse: ``{}`` si se autoriza; si no, registra y niega."""
        if decision.autorizada:
            return {}
        self.estado.negaciones.append(Negacion(herramienta, decision.codigo))
        if decision.pendiente:
            self.estado.pendientes[decision.pendiente] = UMBRAL
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": decision.razon,
            }
        }

    def decidir(self, herramienta: str, argumentos: dict) -> Decision:
        """Orden: identidad, titularidad y, para disputar, umbral."""
        if herramienta not in SOBRE_PRODUCTOS:
            return negar(FALLA_CONTROL)
        verificado = self.estado.cliente_verificado
        if verificado is None:
            return negar(SIN_IDENTIDAD)
        if herramienta != DISPUTAR:
            if _texto(argumentos, "cliente_id") != verificado:
                return negar(CLIENTE_DISTINTO)
            return AUTORIZADA
        if self.politica is None:
            return negar(FALLA_CONTROL)
        transaccion_id = _texto(argumentos, "transaccion_id")
        # Una excepción de la consulta sube a antes_de_herramienta, que niega.
        transaccion = (
            self.buscar_transaccion(transaccion_id) if transaccion_id else None
        )
        if transaccion is None or transaccion.cliente_id != verificado:
            return negar(TRANSACCION_NO_CONFIRMADA)
        # Regla 2 con el monto del core, nunca con un argumento del modelo.
        if self.politica.requiere_analista(transaccion.monto):
            return negar_por_umbral(self.politica, transaccion.id)
        return AUTORIZADA

    async def despues_de_disputar(self, entrada, tool_use_id, contexto) -> dict:
        """PostToolUse: el rechazo del core por umbral o política crea un pendiente."""
        # Un error al leer la respuesta no inventa pendientes.
        with suppress(Exception):
            transaccion_id = _texto(entrada["tool_input"], "transaccion_id")
            respuesta = leer_respuesta(entrada["tool_response"])
            if transaccion_id and respuesta and respuesta["ok"] is False:
                causa = CAUSA_POR_CODIGO_DEL_CORE.get(respuesta["error"]["codigo"])
                if causa:
                    self.estado.pendientes[transaccion_id] = causa
        return {}

    async def despues_de_escalar(self, entrada, tool_use_id, contexto) -> dict:
        """PostToolUse: un escalamiento exitoso limpia los pendientes que cubre.

        Cubre un pendiente si incluye su transacción y su misma causa: así el analista recibe
        el caso completo. Un escalamiento fallido o ilegible no limpia nada.
        """
        with suppress(Exception):
            argumentos = entrada["tool_input"]
            respuesta = leer_respuesta(entrada["tool_response"])
            causa = _texto(argumentos, "causa")
            ids = lista_de_ids(argumentos.get("transacciones")) or []
            if respuesta and respuesta["ok"] is True:
                for transaccion_id in ids:
                    if self.estado.pendientes.get(transaccion_id) == causa:
                        del self.estado.pendientes[transaccion_id]
        return {}

    async def antes_de_terminar(self, entrada, tool_use_id, contexto) -> dict:
        """Stop: con pendientes, impide terminar el turno hasta el tope; luego deja terminar.

        Una falla interna deja terminar: bloquear por un error podría forzar un ciclo, y el
        pendiente que queda lo hace visible la interfaz.
        """
        try:
            pendientes = self.estado.pendientes
            if (
                not pendientes
                or self.estado.cierres_impedidos >= MAXIMO_CIERRES_IMPEDIDOS
            ):
                return {}
            self.estado.cierres_impedidos += 1
            lista = ", ".join(f"{t} (causa {c})" for t, c in sorted(pendientes.items()))
            razon = (
                f"Antes de terminar, escala con escalar_a_analista: {lista}. Incluye el "
                "cliente, las transacciones, las acciones realizadas y la acción recomendada."
            )
        except Exception:  # noqa: BLE001 - falla abierta justificada (research R4)
            return {}
        return {"decision": "block", "reason": razon}

    async def al_recibir_mensaje(self, entrada, tool_use_id, contexto) -> dict:
        """UserPromptSubmit: cada mensaje del cliente empieza sin pendientes ni cierres.

        Un mensaje con ``agent_id`` no es del cliente (viene de un subagente) y no reinicia
        nada: no debe borrar los pendientes del turno del principal.
        """
        with suppress(Exception):
            if isinstance(entrada, dict) and entrada.get("agent_id"):
                return {}
            self.estado.pendientes = {}
            self.estado.cierres_impedidos = 0
        return {}
