"""Un turno del agente: procesa los mensajes del SDK y decide cómo terminó.

El SDK ejecuta las herramientas y vuelve al modelo mientras este responde con razón de parada
``tool_use``; el turno termina cuando el modelo indica fin de turno y llega el
``ResultMessage``. Aquí solo se lee ese flujo y se clasifica el resultado por su subtipo y su
razón de terminación: nunca se cuentan mensajes ni se buscan palabras en el texto.
"""

from collections.abc import AsyncIterable
from dataclasses import dataclass

from claude_agent_sdk import (
    AssistantMessage,
    Message,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

from agente_disputas.configuracion import SERVIDOR

COMPLETADO = "completado"
SALVAGUARDA = "salvaguarda"
FALLA_SERVICIO = "falla_servicio"
ERROR = "error"


@dataclass(frozen=True)
class ResultadoTurno:
    estado: str
    texto: str
    herramientas: tuple[str, ...]
    detalle: str | None  # solo para el registro; nunca se muestra al cliente


def _es_temporal(estado_http: int | None) -> bool:
    """Saturación (429) o falla del servicio (5xx, incluido 529): reintentar puede servir."""
    return estado_http is not None and (estado_http == 429 or estado_http >= 500)


def clasificar(resultado: ResultMessage) -> tuple[str, str | None]:
    """Estado del turno y detalle técnico según cómo terminó el ciclo del SDK."""
    if (
        resultado.subtype == "error_max_turns"
        or resultado.terminal_reason == "max_turns"
    ):
        return SALVAGUARDA, None
    if resultado.is_error and _es_temporal(resultado.api_error_status):
        return FALLA_SERVICIO, f"API respondió {resultado.api_error_status}"
    if resultado.subtype == "success" and not resultado.is_error:
        return COMPLETADO, None
    return ERROR, f"{resultado.subtype}: {resultado.errors or resultado.result}"


async def procesar_turno(mensajes: AsyncIterable[Message]) -> ResultadoTurno:
    """Resultado del turno; el texto es solo el escrito después de la última herramienta.

    Lo que el modelo escribe antes de usar una herramienta es su paso intermedio, no la
    respuesta al cliente, y el texto de un subagente (``parent_tool_use_id``) es para el
    agente principal: ninguno de los dos se muestra.
    """
    textos: list[str] = []
    herramientas: list[str] = []
    async for mensaje in mensajes:
        if isinstance(mensaje, AssistantMessage):
            del_principal = mensaje.parent_tool_use_id is None
            for bloque in mensaje.content:
                if isinstance(bloque, ToolUseBlock):
                    herramientas.append(bloque.name)
                    if del_principal:
                        textos.clear()
                elif (
                    del_principal
                    and isinstance(bloque, TextBlock)
                    and bloque.text.strip()
                ):
                    textos.append(bloque.text.strip())
        elif isinstance(mensaje, ResultMessage):
            estado, detalle = clasificar(mensaje)
            return ResultadoTurno(
                estado, "\n".join(textos), tuple(herramientas), detalle
            )
    return ResultadoTurno(
        ERROR, "\n".join(textos), tuple(herramientas), "el turno terminó sin resultado"
    )


def estado_core(respuesta: dict) -> str:
    """Estado del servidor del core en la respuesta de ``get_mcp_status``, o ``ausente``."""
    for servidor in respuesta.get("mcpServers", []):
        if servidor.get("name") == SERVIDOR:
            return servidor.get("status", "ausente")
    return "ausente"
