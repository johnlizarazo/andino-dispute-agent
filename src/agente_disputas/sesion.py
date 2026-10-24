"""Sesión de chat: una conversación de la interfaz con su propio agente y controles (#12).

El SDK no admite usar un mismo ``ClaudeSDKClient`` desde tareas distintas, y la interfaz
atiende cada mensaje en una tarea propia. Por eso cada sesión tiene un trabajador, dueño del
cliente, que atiende los mensajes de una cola de a uno (research R3). Los eventos del turno
viajan por una cola propia del pedido y ``turno`` los entrega en la tarea de quien lo llama.
Los avisos son los de la línea de comandos: ningún error llega al cliente como traza.
"""

import asyncio
from collections.abc import Awaitable, Callable, Mapping

from claude_agent_sdk import ClaudeSDKClient

from agente_disputas.ciclo import COMPLETADO, procesar_turno
from agente_disputas.cli import (
    AVISO_ESCALAMIENTO_PENDIENTE,
    AVISO_SESION,
    AVISOS,
    SIN_TEXTO,
    esperar_core,
)
from agente_disputas.configuracion import (
    CredencialFaltanteError,
    crear_opciones,
    validar_credencial,
)
from agente_disputas.controles import Controles
from agente_disputas.eventos import Evento, LectorEventos

AVISO_SIN_CORE = "El core bancario no arrancó; revisa su configuración."
AVISO_ARRANQUE = "No se pudo iniciar el agente; inténtalo de nuevo."

AlEvento = Callable[[Evento], Awaitable[None]]


class _Fin:
    """Marca el final de un turno en la cola de su pedido, con el texto para el cliente."""

    def __init__(self, texto: str):
        self.texto = texto


class SesionChat:
    def __init__(
        self,
        entorno: Mapping[str, str],
        fabrica_cliente=ClaudeSDKClient,
        controles: Controles | None = None,
    ):
        self.entorno = dict(entorno)
        self.fabrica_cliente = fabrica_cliente
        self.controles = controles or Controles.desde_entorno(self.entorno)
        self._pedidos: asyncio.Queue | None = None
        self._trabajador: asyncio.Task | None = None
        # Aviso con el que se responde todo mensaje cuando la sesión no puede atender.
        self._no_disponible: str | None = None

    async def iniciar(self) -> str | None:
        """Arranca el agente; devuelve el aviso si no puede atender o ``None`` si quedó lista."""
        try:
            validar_credencial(self.entorno)
        except CredencialFaltanteError as error:
            self._no_disponible = str(error)
            return self._no_disponible
        self._pedidos = asyncio.Queue()
        lista = asyncio.get_running_loop().create_future()
        self._trabajador = asyncio.create_task(self._trabajar(lista))
        self._no_disponible = await lista
        return self._no_disponible

    async def turno(self, texto: str, al_evento: AlEvento) -> str:
        """Atiende un mensaje: entrega sus eventos en orden y devuelve la respuesta final."""
        if self._no_disponible is not None:
            return self._no_disponible
        if self._pedidos is None:
            return AVISO_SESION
        salida: asyncio.Queue = asyncio.Queue()
        await self._pedidos.put((texto, salida))
        while True:
            elemento = await salida.get()
            if isinstance(elemento, _Fin):
                return elemento.texto
            await al_evento(elemento)

    async def cerrar(self) -> None:
        """Termina el trabajador, que sale del contexto del cliente; se puede repetir."""
        if self._no_disponible is None:
            self._no_disponible = AVISO_SESION
        if self._trabajador is None:
            return
        if not self._trabajador.done():
            await self._pedidos.put(None)
        await asyncio.gather(self._trabajador, return_exceptions=True)
        self._trabajador = None

    async def _trabajar(self, lista: asyncio.Future) -> None:
        opciones = crear_opciones(self.entorno, self.controles)
        try:
            async with self.fabrica_cliente(options=opciones) as cliente:
                if await esperar_core(cliente) != "connected":
                    lista.set_result(AVISO_SIN_CORE)
                    return
                lista.set_result(None)
                await self._atender(cliente)
        except Exception:  # noqa: BLE001 - cualquier falla al arrancar se avisa sin traza
            if not lista.done():
                lista.set_result(AVISO_ARRANQUE)
        finally:
            self._vaciar()

    async def _atender(self, cliente) -> None:
        while (pedido := await self._pedidos.get()) is not None:
            texto, salida = pedido
            try:
                respuesta = await self._un_turno(cliente, texto, salida)
            except Exception:  # noqa: BLE001 - sesión perdida: avisar en vez de colgar el turno
                self._no_disponible = AVISO_SESION
                await salida.put(_Fin(AVISO_SESION))
                return
            await salida.put(_Fin(respuesta))

    async def _un_turno(self, cliente, texto: str, salida: asyncio.Queue) -> str:
        lector = LectorEventos(self.controles.estado)

        async def con_eventos(mensajes):
            async for mensaje in mensajes:
                for evento in lector.leer(mensaje):
                    await salida.put(evento)
                yield mensaje

        await cliente.query(texto)
        resultado = await procesar_turno(con_eventos(cliente.receive_response()))
        for evento in lector.cerrar():
            await salida.put(evento)
        if resultado.estado == COMPLETADO:
            respuesta = resultado.texto or SIN_TEXTO
        else:
            respuesta = AVISOS[resultado.estado]
        if self.controles.estado.pendientes:
            respuesta += "\n\n" + AVISO_ESCALAMIENTO_PENDIENTE
        return respuesta

    def _vaciar(self) -> None:
        """Al terminar el trabajador, los pedidos que quedaron reciben el aviso de sesión."""
        if self._no_disponible is None:
            self._no_disponible = AVISO_SESION
        while self._pedidos is not None and not self._pedidos.empty():
            pedido = self._pedidos.get_nowait()
            if pedido is not None:
                pedido[1].put_nowait(_Fin(AVISO_SESION))
