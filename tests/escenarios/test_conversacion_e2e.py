"""Escenarios de punta a punta: llaman al modelo real (requieren ANTHROPIC_API_KEY).

Los mensajes del cliente son distintos de cualquier ejemplo del prompt de sistema, para que
un escenario no pase por memoria (principio VI).
"""

import asyncio
import os
import time
from dataclasses import replace

import pytest
from claude_agent_sdk import ClaudeSDKClient

from agente_disputas.ciclo import COMPLETADO, ResultadoTurno, procesar_turno
from agente_disputas.configuracion import VARIABLE_FALLAS, crear_opciones
from agente_disputas.controles import DISPUTAR, Controles

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY", "").strip(),
        reason="requiere ANTHROPIC_API_KEY",
    ),
]

BUSCAR = "mcp__core-bancario__buscar_cliente"
MENSAJE = (
    "Buenas tardes. Quiero revisar unos movimientos de mi cuenta; "
    "mi número de documento es CC-FIC-0002."
)


def _un_turno(fallas: str) -> ResultadoTurno:
    entorno = {**os.environ, VARIABLE_FALLAS: fallas}

    async def conversar() -> ResultadoTurno:
        async with ClaudeSDKClient(options=crear_opciones(entorno)) as cliente:
            await cliente.query(MENSAJE)
            return await procesar_turno(cliente.receive_response())

    inicio = time.perf_counter()
    resultado = asyncio.run(conversar())
    # Dato para SC-005 (primera respuesta en menos de 30 s); no hace fallar el escenario.
    print(f"\n[{fallas}] turno resuelto en {time.perf_counter() - inicio:.1f} s")
    return resultado


def test_falla_transitoria_se_reintenta_y_el_turno_se_completa():
    resultado = _un_turno("buscar_cliente:1")
    assert resultado.estado == COMPLETADO
    assert resultado.herramientas.count(BUSCAR) >= 2
    assert "FALLA_TRANSITORIA" not in resultado.texto


def test_falla_persistente_se_rinde_y_ofrece_escalar():
    resultado = _un_turno("buscar_cliente:5")
    texto = resultado.texto.lower()
    assert resultado.estado == COMPLETADO
    assert resultado.herramientas.count(BUSCAR) <= 3
    assert any(palabra in texto for palabra in ("analista", "persona", "escal"))
    assert "falla_transitoria" not in texto


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
