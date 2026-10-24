"""Interfaz de chat con Chainlit (#12): única pieza que importa Chainlit.

Arranque: ``uv run andino-chat`` (``main``). Cada conversación tiene su ``SesionChat``
(agente y controles propios); aquí solo se traduce a mensajes de Chainlit: los eventos del
turno con autor ``Evento`` y la respuesta con autor ``Agente``.
"""

import os
import sys
from pathlib import Path

import chainlit as cl

from agente_disputas.eventos import Evento, formatear_evento
from agente_disputas.sesion import SesionChat

AUTOR_AGENTE = "Agente"
AUTOR_EVENTO = "Evento"
CLAVE_SESION = "sesion"
BIENVENIDA_WEB = (
    "Agente de disputas de Banco Andino (ficticio). Escribe tu mensaje para empezar; "
    "los eventos importantes de la conversación aparecen como mensajes de «Evento»."
)


async def _enviar_evento(evento: Evento) -> None:
    await cl.Message(content=formatear_evento(evento), author=AUTOR_EVENTO).send()


@cl.on_chat_start
async def al_iniciar() -> None:
    sesion = SesionChat(os.environ)
    cl.user_session.set(CLAVE_SESION, sesion)
    aviso = await sesion.iniciar()
    await cl.Message(content=aviso or BIENVENIDA_WEB, author=AUTOR_AGENTE).send()


@cl.on_message
async def al_recibir(mensaje: cl.Message) -> None:
    sesion: SesionChat = cl.user_session.get(CLAVE_SESION)
    respuesta = await sesion.turno(mensaje.content, _enviar_evento)
    await cl.Message(content=respuesta, author=AUTOR_AGENTE).send()


@cl.on_chat_end
async def al_terminar() -> None:
    sesion: SesionChat | None = cl.user_session.get(CLAVE_SESION)
    if sesion is not None:
        await sesion.cerrar()


def main() -> None:
    """Arranca esta interfaz con el CLI de Chainlit, sin ``nest_asyncio`` (research R5).

    El CLI de Chainlit aplica ``nest_asyncio`` al importarse; en Python 3.14 eso impide que
    anyio detecte el event loop y toda petición HTTP falla. La interfaz es asíncrona de punta
    a punta y no necesita reentrada, así que se neutraliza antes de importar el CLI.
    """
    import nest_asyncio

    nest_asyncio.apply = lambda *_args, **_kwargs: None
    from chainlit.cli import cli

    cli(["run", str(Path(__file__).resolve()), *sys.argv[1:]])
