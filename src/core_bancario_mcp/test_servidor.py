import asyncio
import os
import subprocess
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from core_bancario_mcp.fallas import VARIABLE
from core_bancario_mcp.servidor import crear_servidor


def _entorno(**extra: str) -> dict[str, str]:
    entorno = {k: v for k, v in os.environ.items() if k != VARIABLE}
    return {**entorno, **extra}


def test_servidor_se_llama_core_bancario_y_aun_no_tiene_herramientas():
    servidor = crear_servidor()
    assert servidor.name == "core-bancario"
    assert asyncio.run(servidor.list_tools()) == []


async def _arrancar_y_listar() -> tuple[float, list]:
    parametros = StdioServerParameters(
        command=sys.executable, args=["-m", "core_bancario_mcp"], env=_entorno()
    )
    inicio = time.perf_counter()
    async with (
        stdio_client(parametros) as (lectura, escritura),
        ClientSession(lectura, escritura) as sesion,
    ):
        await sesion.initialize()
        listo = time.perf_counter() - inicio
        herramientas = await sesion.list_tools()
    return listo, herramientas.tools


def test_arranque_real_por_stdio_responde_a_tiempo():
    listo, herramientas = asyncio.run(
        asyncio.wait_for(_arrancar_y_listar(), timeout=10)
    )
    assert herramientas == []
    assert listo < 5, f"el servidor tardó {listo:.1f} s en estar listo (objetivo: 5 s)"


def test_configuracion_de_fallas_invalida_impide_arrancar():
    r = subprocess.run(
        [sys.executable, "-m", "core_bancario_mcp"],
        capture_output=True,
        check=False,
        timeout=30,
        env=_entorno(**{VARIABLE: "op:0"}),
    )
    assert r.returncode == 1
    assert VARIABLE in r.stderr.decode("utf-8")
