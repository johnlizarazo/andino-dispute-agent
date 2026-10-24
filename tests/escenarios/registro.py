"""Registro de lo que hizo el agente en un turno, para comprobarlo sin mirar el texto (#13).

``conversar`` habla con el agente real (mismas opciones, controles y core que el producto) y
devuelve un ``Registro``: las herramientas que usó el agente principal, en orden, con sus
argumentos, la respuesta del core leída con su contrato y la negación del control si la hubo,
más los escalamientos pendientes al terminar. ``armar_registro`` es la parte pura y se prueba
sin API (research R1).
"""

import asyncio
import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from agente_disputas.ciclo import ResultadoTurno, procesar_turno
from agente_disputas.configuracion import crear_opciones
from agente_disputas.controles import Controles, EstadoSesion, leer_respuesta

PREFIJO = "mcp__core-bancario__"


@dataclass(frozen=True)
class Llamada:
    herramienta: str
    argumentos: dict
    respuesta: dict | None
    negada: str | None

    @property
    def ok(self) -> bool:
        return self.respuesta is not None and self.respuesta.get("ok") is True

    @property
    def codigo(self) -> str | None:
        if self.respuesta is None or self.respuesta.get("ok") is not False:
            return None
        return (self.respuesta.get("error") or {}).get("codigo")


@dataclass(frozen=True)
class Registro:
    llamadas: list[Llamada]
    pendientes: dict
    estado: str
    texto: str = field(repr=False)

    def de(self, herramienta: str) -> list[Llamada]:
        return [ll for ll in self.llamadas if ll.herramienta == herramienta]

    def primera(self) -> Llamada | None:
        return self.llamadas[0] if self.llamadas else None

    def escalamientos(self, causa: str) -> list[Llamada]:
        return [
            ll
            for ll in self.de("escalar_a_analista")
            if ll.ok and ll.argumentos.get("causa") == causa
        ]

    def resumen(self) -> str:
        """Las llamadas en una línea cada una, para el mensaje de una aserción fallida."""
        lineas = [
            f"{ll.herramienta}({ll.argumentos}) -> "
            f"{'ok' if ll.ok else ll.codigo or ll.negada or 'sin respuesta'}"
            for ll in self.llamadas
        ]
        return "\n".join(lineas) or "(sin llamadas)"


def armar_registro(
    mensajes: list,
    estado: EstadoSesion,
    inicio_negaciones: int,
    resultado: ResultadoTurno,
) -> Registro:
    negadas = {
        n.tool_use_id: n.codigo
        for n in estado.negaciones[inicio_negaciones:]
        if n.tool_use_id
    }
    usos: dict[str, ToolUseBlock] = {}
    respuestas: dict[str, dict | None] = {}
    for mensaje in mensajes:
        # Solo el agente principal: el subagente trae parent_tool_use_id.
        if not isinstance(mensaje, AssistantMessage | UserMessage):
            continue
        if mensaje.parent_tool_use_id is not None or not isinstance(
            mensaje.content, list
        ):
            continue
        for bloque in mensaje.content:
            if isinstance(bloque, ToolUseBlock):
                usos[bloque.id] = bloque
            elif isinstance(bloque, ToolResultBlock) and bloque.tool_use_id in usos:
                respuestas[bloque.tool_use_id] = leer_respuesta(bloque.content)
    llamadas = [
        Llamada(
            herramienta=uso.name.removeprefix(PREFIJO),
            argumentos=uso.input if isinstance(uso.input, dict) else {},
            respuesta=respuestas.get(uso_id),
            negada=negadas.get(uso_id),
        )
        for uso_id, uso in usos.items()
    ]
    return Registro(
        llamadas, dict(estado.pendientes), resultado.estado, resultado.texto
    )


def conversar(mensaje: str, entorno: Mapping[str, str] | None = None) -> Registro:
    """Un turno con el agente real y su registro de operaciones."""
    entorno = dict(os.environ if entorno is None else entorno)
    controles = Controles.desde_entorno(entorno)
    inicio = len(controles.estado.negaciones)
    mensajes: list = []

    async def guardar(flujo):
        async for m in flujo:
            mensajes.append(m)
            yield m

    async def un_turno() -> ResultadoTurno:
        async with ClaudeSDKClient(
            options=crear_opciones(entorno, controles)
        ) as cliente:
            await cliente.query(mensaje)
            return await procesar_turno(guardar(cliente.receive_response()))

    resultado = asyncio.run(un_turno())
    return armar_registro(mensajes, controles.estado, inicio, resultado)
