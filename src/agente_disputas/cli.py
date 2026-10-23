"""Línea de comandos para conversar con el agente turno a turno.

``main`` valida la credencial, arranca el agente con el core bancario y comprueba que el core
quedó conectado; ``conversar`` lee un mensaje por línea y muestra la respuesta según cómo
terminó el turno. Ningún error llega al cliente como traza ni con datos técnicos.
"""

import asyncio
import os
import sys

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeSDKError,
    CLIConnectionError,
    CLINotFoundError,
    ProcessError,
)

from agente_disputas.ciclo import (
    COMPLETADO,
    ERROR,
    FALLA_SERVICIO,
    SALVAGUARDA,
    estado_core,
    procesar_turno,
)
from agente_disputas.configuracion import (
    CredencialFaltanteError,
    crear_opciones,
    validar_credencial,
)

ORDEN_SALIDA = "/salir"
BIENVENIDA = (
    "Agente de disputas de Banco Andino (ficticio). Escribe tu mensaje; "
    f"{ORDEN_SALIDA} para terminar."
)
DESPEDIDA = "Hasta pronto."
AVISO_SALVAGUARDA = "No pude terminar de atender tu solicitud. Si quieres, puedo pasarte con una persona."
AVISO_FALLA_SERVICIO = "Tuvimos un problema temporal. Por favor, escribe tu mensaje de nuevo en un momento."
AVISO_ERROR = (
    "Ocurrió un problema al procesar tu mensaje. Por favor, inténtalo de nuevo."
)
AVISO_SESION = (
    "La conversación no puede continuar por un problema técnico. Hasta pronto."
)
SIN_TEXTO = "(Sin respuesta del agente.)"
ESPERA_CORE_SEGUNDOS = 15

AVISOS = {
    SALVAGUARDA: AVISO_SALVAGUARDA,
    FALLA_SERVICIO: AVISO_FALLA_SERVICIO,
    ERROR: AVISO_ERROR,
}


async def conversar(cliente, leer, escribir) -> int:
    """Bucle turno a turno; termina con ``/salir``, fin de entrada o Ctrl+C."""
    while True:
        try:
            linea = leer().strip()
        except EOFError, KeyboardInterrupt:
            escribir(DESPEDIDA)
            return 0
        if not linea:
            continue
        if linea == ORDEN_SALIDA:
            escribir(DESPEDIDA)
            return 0
        try:
            await cliente.query(linea)
            resultado = await procesar_turno(cliente.receive_response())
        except ClaudeSDKError:
            escribir(AVISO_SESION)
            return 1
        if resultado.estado == COMPLETADO:
            escribir(resultado.texto or SIN_TEXTO)
        else:
            escribir(AVISOS[resultado.estado])


async def _esperar_core(cliente) -> str:
    """Estado final del core tras arrancar (espera mientras esté ``pending``)."""
    estado = "pending"
    for _ in range(ESPERA_CORE_SEGUNDOS * 2):
        estado = estado_core(await cliente.get_mcp_status())
        if estado != "pending":
            break
        await asyncio.sleep(0.5)
    return estado


async def _ejecutar(entorno) -> int:
    async with ClaudeSDKClient(options=crear_opciones(entorno)) as cliente:
        if await _esperar_core(cliente) != "connected":
            print(
                "El core bancario no arrancó; revisa su configuración.", file=sys.stderr
            )
            return 1
        print(BIENVENIDA)
        return await conversar(cliente, lambda: input("> "), print)


def main() -> int:
    entorno = dict(os.environ)
    try:
        validar_credencial(entorno)
    except CredencialFaltanteError as error:
        print(str(error), file=sys.stderr)
        return 1
    try:
        return asyncio.run(_ejecutar(entorno))
    except KeyboardInterrupt:
        print(DESPEDIDA)
        return 0
    except CLINotFoundError:
        print("No se encontró el motor del agente (Claude Code).", file=sys.stderr)
    except CLIConnectionError, ProcessError:
        print("No se pudo iniciar el agente; inténtalo de nuevo.", file=sys.stderr)
    return 1
