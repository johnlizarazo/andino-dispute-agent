import asyncio
import json
import os
import subprocess
import sys
import time

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from core_bancario_mcp.fallas import VARIABLE
from core_bancario_mcp.servidor import crear_servidor

HERRAMIENTAS = ["buscar_cliente", "verificar_identidad"]


def _entorno(**extra: str) -> dict[str, str]:
    entorno = {k: v for k, v in os.environ.items() if k != VARIABLE}
    return {**entorno, **extra}


@pytest.fixture(scope="module")
def herramientas() -> dict:
    lista = asyncio.run(crear_servidor().list_tools())
    return {h.name: h for h in lista}


def _llamar(servidor, nombre: str, argumentos: dict) -> dict:
    (contenido,) = asyncio.run(servidor.call_tool(nombre, argumentos))
    return json.loads(contenido.text)


def test_servidor_publica_exactamente_las_herramientas_de_identificacion(herramientas):
    assert crear_servidor().name == "core-bancario"
    assert sorted(herramientas) == HERRAMIENTAS


def test_descripcion_de_buscar_dice_que_no_verifica_ni_elige(herramientas):
    descripcion = herramientas["buscar_cliente"].description.lower()
    assert "no verifica" in descripcion
    assert "varias coincidencias" in descripcion
    assert "no elijas" in descripcion
    assert "otro identificador" in descripcion


def test_descripcion_de_verificar_dice_cuando_usarla(herramientas):
    descripcion = herramientas["verificar_identidad"].description.lower()
    assert "una única coincidencia" in descripcion
    assert "no reintentes" in descripcion
    assert "inventado" in descripcion


def test_parametros_se_publican_como_texto(herramientas):
    assert herramientas
    for herramienta in herramientas.values():
        propiedades = herramienta.inputSchema["properties"]
        assert propiedades
        assert all(p["type"] == "string" for p in propiedades.values())


def test_call_tool_responde_con_el_contrato():
    respuesta = _llamar(crear_servidor(), "buscar_cliente", {"nombre": "carlos perez"})
    assert respuesta["ok"] is True
    assert len(respuesta["datos"]) == 2


def test_tipo_json_incorrecto_se_responde_con_el_contrato():
    respuesta = _llamar(crear_servidor(), "buscar_cliente", {"ultimos4": 4821})
    assert respuesta["ok"] is False
    assert respuesta["error"]["codigo"] == "PARAMETRO_INVALIDO"


def test_servidor_no_cuelga_atributos_al_vuelo():
    servidor = crear_servidor()
    assert not hasattr(servidor, "repositorio")
    assert not hasattr(servidor, "inyector")


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
    assert sorted(h.name for h in herramientas) == HERRAMIENTAS
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
