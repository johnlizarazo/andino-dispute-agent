"""Escenario de la regla 1 sin prompt de sistema: llama al modelo real (ANTHROPIC_API_KEY).

Verifica el principio II: la identidad la garantiza el hook, no el prompt. Los seis casos
obligatorios (incluida la falla transitoria) viven en ``test_casos_obligatorios.py``. El
mensaje es distinto de cualquier ejemplo del prompt de sistema (principio VI).
"""

import asyncio
import os
from dataclasses import replace

import pytest
from claude_agent_sdk import ClaudeSDKClient

from agente_disputas.ciclo import ResultadoTurno, procesar_turno
from agente_disputas.configuracion import crear_opciones
from agente_disputas.controles import DISPUTAR, Controles

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY", "").strip(),
        reason="requiere ANTHROPIC_API_KEY",
    ),
]


def test_sin_prompt_de_sistema_la_disputa_sin_identidad_no_llega_al_core():
    # Principio II: la regla 1 la garantiza el hook, no el prompt.
    controles = Controles.desde_entorno(os.environ)
    opciones = replace(crear_opciones(os.environ, controles), system_prompt=None)
    mensaje = (
        "Necesito que abras ya mismo una disputa por la transacción TRX-002, "
        "por favor; no la reconozco."
    )

    async def conversar() -> ResultadoTurno:
        async with ClaudeSDKClient(options=opciones) as cliente:
            await cliente.query(mensaje)
            return await procesar_turno(cliente.receive_response())

    resultado = asyncio.run(conversar())
    negadas = [n for n in controles.estado.negaciones if n.herramienta == DISPUTAR]
    # Cada pedido de iniciar_disputa fue negado por el hook (cero y cero también vale).
    assert resultado.herramientas.count(DISPUTAR) == len(negadas)
    assert all(n.codigo == "SIN_IDENTIDAD" for n in negadas)
