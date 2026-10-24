"""Controles del agente: hooks del SDK que garantizan las reglas 1 y 2 (principio II).

Un hook ``PostToolUse`` sobre ``verificar_identidad`` registra en el estado de la
conversación el cliente verificado; un hook ``PreToolUse`` sobre las herramientas que operan
sobre productos niega sin identidad verificada, sobre productos de otro cliente o con una
disputa por encima del umbral. El monto y el titular se leen de los datos del core por el
``transaccion_id``, nunca de otro argumento del modelo. Los controles fallan cerrado: si no
pueden obtener el dato o algo falla, niegan. No leen el prompt de sistema.
"""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from claude_agent_sdk import HookMatcher

from core_bancario_mcp.fallas import VARIABLE as VARIABLE_FALLAS
from core_bancario_mcp.fallas import InyectorFallas
from core_bancario_mcp.repositorio import Politica, Repositorio, Transaccion

PREFIJO = "mcp__core-bancario__"
CONSULTAR = PREFIJO + "consultar_transacciones"
DISPUTAR = PREFIJO + "iniciar_disputa"
BLOQUEAR = PREFIJO + "bloquear_tarjeta"
VERIFICAR = PREFIJO + "verificar_identidad"
SOBRE_PRODUCTOS = (CONSULTAR, DISPUTAR, BLOQUEAR)
# Operación de CORE_BANCARIO_FALLAS que hace fallar la consulta de datos del control.
OPERACION_FALLAS = "control_transaccion"
# Los controles son consultas en memoria; el tope solo evita esperar de más.
TIEMPO_MAXIMO_SEGUNDOS = 10

SIN_IDENTIDAD = "SIN_IDENTIDAD"
CLIENTE_DISTINTO = "CLIENTE_DISTINTO"
TRANSACCION_NO_CONFIRMADA = "TRANSACCION_NO_CONFIRMADA"
REQUIERE_ANALISTA = "REQUIERE_ANALISTA"
FALLA_CONTROL = "FALLA_CONTROL"
# Las razones nunca nombran a otro cliente ni dicen si una transacción existe.
RAZONES = {
    SIN_IDENTIDAD: "Primero verifica la identidad del cliente con verificar_identidad.",
    CLIENTE_DISTINTO: (
        "Solo puedes operar sobre productos del cliente verificado en esta conversación."
    ),
    TRANSACCION_NO_CONFIRMADA: (
        "No se pudo confirmar que esa transacción pertenezca al cliente verificado."
    ),
    REQUIERE_ANALISTA: (
        "Esta disputa supera $500.000 y requiere un analista humano: escala el caso."
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


AUTORIZADA = Decision(True)


def negar(codigo: str) -> Decision:
    return Decision(False, codigo, RAZONES[codigo])


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
                )
            ],
            "PostToolUse": [
                HookMatcher(
                    matcher=VERIFICAR,
                    hooks=[self.despues_de_verificar],
                    timeout=TIEMPO_MAXIMO_SEGUNDOS,
                )
            ],
        }

    async def despues_de_verificar(self, entrada, tool_use_id, contexto) -> dict:
        """PostToolUse: solo un éxito explícito del core, para el cliente pedido, registra."""
        try:
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
        except Exception:  # noqa: BLE001 - falla cerrada: cualquier error no registra
            return {}
        return {}

    async def antes_de_herramienta(self, entrada, tool_use_id, contexto) -> dict:
        """PreToolUse: autoriza solo si pasan todas las comprobaciones; si no, niega."""
        herramienta = None
        try:
            herramienta = entrada["tool_name"]
            decision = self.decidir(herramienta, entrada["tool_input"])
        except Exception:  # noqa: BLE001 - falla cerrada: cualquier error niega
            decision = negar(FALLA_CONTROL)
        if decision.autorizada:
            return {}
        self.estado.negaciones.append(Negacion(str(herramienta), decision.codigo))
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
            return negar(REQUIERE_ANALISTA)
        return AUTORIZADA
