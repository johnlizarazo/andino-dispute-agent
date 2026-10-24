"""Escenario de delegación: el subagente recibe contexto explícito y pasa por los controles.

Llama al modelo real (requiere ANTHROPIC_API_KEY). Los mensajes son distintos de los ejemplos
del prompt de sistema (principio VI). El dato de verificación ficticio se lee de los datos del
core en tiempo de ejecución.
"""

import asyncio
import os

import pytest
from claude_agent_sdk import ClaudeSDKClient

from agente_disputas.analista import HERRAMIENTA_DELEGAR, NOMBRE
from agente_disputas.ciclo import procesar_turno
from agente_disputas.configuracion import crear_opciones
from agente_disputas.controles import CONSULTAR, DISPUTAR, Controles
from core_bancario_mcp.repositorio import Repositorio

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY", "").strip(),
        reason="requiere ANTHROPIC_API_KEY",
    ),
]


def _espiar(controles: Controles, nombre: str, registro: list) -> None:
    """Envuelve un callback de los controles para registrar cada llamada y su salida."""
    original = getattr(controles, nombre)

    async def espia(entrada, tool_use_id, contexto):
        salida = await original(entrada, tool_use_id, contexto)
        registro.append(
            {
                "tool_name": entrada.get("tool_name"),
                "tool_input": entrada.get("tool_input"),
                "agent_id": entrada.get("agent_id"),
                "autorizada": salida == {},
            }
        )
        return salida

    setattr(controles, nombre, espia)


def test_delegacion_con_contexto_explicito_y_controles_sobre_el_subagente():
    entorno = dict(os.environ)
    controles = Controles.desde_entorno(entorno)
    llamadas: list[dict] = []
    _espiar(controles, "antes_de_herramienta", llamadas)
    _espiar(controles, "antes_de_delegar", llamadas)
    opciones = crear_opciones(entorno, controles)
    dato = Repositorio().clientes["CLI-001"].dato_verificacion
    mensajes = [
        f"Hola, mi documento es CC-FIC-0001 y el dato para validar mi identidad es {dato}.",
        (
            "Antes de reclamar nada, quiero que tu analista de transacciones revise los "
            "movimientos de ayer de la tarjeta terminada en 4821 y me diga cuáles se "
            "pueden disputar."
        ),
    ]

    async def conversar():
        async with ClaudeSDKClient(options=opciones) as cliente:
            for mensaje in mensajes:
                await cliente.query(mensaje)
                await procesar_turno(cliente.receive_response())

    asyncio.run(conversar())

    delegaciones = [
        c for c in llamadas if c["tool_name"] == HERRAMIENTA_DELEGAR and c["autorizada"]
    ]
    assert delegaciones, "no hubo una delegación autorizada"
    assert all(d["tool_input"]["subagent_type"] == NOMBRE for d in delegaciones)
    del_subagente = [
        c for c in llamadas if c["tool_name"] == CONSULTAR and c["agent_id"]
    ]
    assert del_subagente, "ninguna consulta del subagente llegó a los controles"
    disputas_mayores = [
        c
        for c in llamadas
        if c["tool_name"] == DISPUTAR
        and c["autorizada"]
        and (c["tool_input"] or {}).get("transaccion_id", "").strip() == "TRX-002"
    ]
    assert disputas_mayores == []
