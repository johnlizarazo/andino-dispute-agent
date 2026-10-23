import asyncio
import json
import shutil
from datetime import date
from pathlib import Path

import pytest
from mcp.server.fastmcp import FastMCP

from core_bancario_mcp.contexto import Contexto
from core_bancario_mcp.fallas import InyectorFallas
from core_bancario_mcp.identificacion import (
    buscar_cliente,
    registrar,
    verificar_identidad,
)
from core_bancario_mcp.repositorio import Repositorio

DATOS = Path(__file__).with_name("datos")
HOY = date(2026, 10, 23)


@pytest.fixture
def contexto() -> Contexto:
    return Contexto(Repositorio(hoy=HOY), InyectorFallas(None))


def _ids(respuesta: dict) -> list[str]:
    assert respuesta["ok"] is True
    return [c["cliente_id"] for c in respuesta["datos"]]


def _es_validacion(respuesta: dict) -> bool:
    return (
        respuesta["ok"] is False
        and respuesta["error"]["tipo"] == "validacion"
        and respuesta["error"]["codigo"] == "PARAMETRO_INVALIDO"
        and respuesta["error"]["reintentable"] is False
    )


# --- buscar_cliente ---


def test_buscar_por_documento_devuelve_una_coincidencia(contexto):
    assert _ids(buscar_cliente(contexto, documento="CC-FIC-0001")) == ["CLI-001"]


def test_buscar_por_ultimos4_devuelve_al_titular(contexto):
    assert _ids(buscar_cliente(contexto, ultimos4="4821")) == ["CLI-001"]


@pytest.mark.parametrize(
    "nombre",
    ["Carlos Andrés Pérez", "carlos perez", "CARLOS ANDRES PEREZ", "Pérez,"],
)
def test_buscar_homonimos_devuelve_los_dos_sin_elegir(contexto, nombre):
    assert _ids(buscar_cliente(contexto, nombre=nombre)) == ["CLI-002", "CLI-003"]


def test_buscar_por_nombre_usa_palabras_completas(contexto):
    assert _ids(buscar_cliente(contexto, nombre="an")) == []


def test_buscar_sin_coincidencias_es_exito_con_lista_vacia(contexto):
    assert buscar_cliente(contexto, documento="CC-FIC-0099") == {
        "ok": True,
        "datos": [],
    }


@pytest.mark.parametrize(
    "criterio",
    [
        {"documento": "CC-FIC-0002"},
        {"nombre": "carlos perez"},
        {"nombre": "Laura"},
        {"ultimos4": "3344"},
    ],
)
def test_coincidencias_solo_exponen_id_y_nombre(contexto, criterio):
    respuesta = buscar_cliente(contexto, **criterio)
    assert respuesta["datos"]
    for coincidencia in respuesta["datos"]:
        assert set(coincidencia) == {"cliente_id", "nombre"}


@pytest.mark.parametrize(
    "criterio",
    [
        {},
        {"documento": "CC-FIC-0001", "nombre": "Laura"},
        {"nombre": ""},
        {"ultimos4": "   "},
        {"documento": "CC-0001"},
        {"ultimos4": "48a1"},
        {"ultimos4": "482"},
        {"ultimos4": 4821},
        {"ultimos4": ["4821"]},
        {"nombre": "a"},
        {"nombre": "x" * 101},
    ],
)
def test_criterios_invalidos_son_error_de_validacion(contexto, criterio):
    assert _es_validacion(buscar_cliente(contexto, **criterio))


def test_ultimos4_compartidos_devuelven_todos_los_titulares(tmp_path):
    carpeta = tmp_path / "datos"
    shutil.copytree(DATOS, carpeta)
    ruta = carpeta / "tarjetas.json"
    tarjetas = json.loads(ruta.read_text(encoding="utf-8"))
    tarjetas += [
        {
            "id": "TAR-901",
            "cliente_id": "CLI-004",
            "ultimos4": "4821",
            "estado": "activa",
        },
        {
            "id": "TAR-902",
            "cliente_id": "CLI-004",
            "ultimos4": "4821",
            "estado": "activa",
        },
    ]
    ruta.write_text(json.dumps(tarjetas), encoding="utf-8")
    contexto = Contexto(Repositorio(hoy=HOY, carpeta=carpeta), InyectorFallas(None))
    assert _ids(buscar_cliente(contexto, ultimos4="4821")) == ["CLI-001", "CLI-004"]


# --- verificar_identidad ---


def _dato(contexto: Contexto, cliente_id: str) -> str:
    return contexto.repositorio.clientes[cliente_id].dato_verificacion


def _incorrecto(contexto: Contexto, cliente_id: str) -> str:
    """Un dato de 4 dígitos distinto del correcto."""
    return f"{(int(_dato(contexto, cliente_id)) + 1) % 10000:04d}"


def _error(respuesta: dict, tipo: str, codigo: str) -> bool:
    return (
        respuesta["ok"] is False
        and respuesta["error"]["tipo"] == tipo
        and respuesta["error"]["codigo"] == codigo
        and respuesta["error"]["reintentable"] is False
    )


def test_verificar_con_dato_correcto_confirma_la_identidad(contexto):
    respuesta = verificar_identidad(contexto, "CLI-001", _dato(contexto, "CLI-001"))
    assert respuesta == {
        "ok": True,
        "datos": {"cliente_id": "CLI-001", "verificado": True},
    }


def test_verificar_con_dato_incorrecto_es_permiso_sin_revelar_el_dato(contexto):
    respuesta = verificar_identidad(
        contexto, "CLI-001", _incorrecto(contexto, "CLI-001")
    )
    assert _error(respuesta, "permiso", "VERIFICACION_FALLIDA")
    assert _dato(contexto, "CLI-001") not in respuesta["error"]["mensaje"]


def test_verificar_cliente_inexistente_es_validacion(contexto):
    respuesta = verificar_identidad(contexto, "CLI-999", "1234")
    assert _error(respuesta, "validacion", "NO_ENCONTRADO")


@pytest.mark.parametrize(
    "argumentos",
    [
        {},
        {"cliente_id": "CLI-001"},
        {"dato_verificacion": "1234"},
        {"cliente_id": "", "dato_verificacion": "1234"},
        {"cliente_id": "CLI-001", "dato_verificacion": "  "},
        {"cliente_id": "CLI-001", "dato_verificacion": 1987},
        {"cliente_id": ["CLI-001"], "dato_verificacion": "1987"},
    ],
)
def test_verificar_parametros_invalidos_son_validacion(contexto, argumentos):
    assert _es_validacion(verificar_identidad(contexto, **argumentos))


def test_tres_fallos_bloquean_aunque_el_cuarto_dato_sea_correcto(contexto):
    for _ in range(3):
        respuesta = verificar_identidad(
            contexto, "CLI-004", _incorrecto(contexto, "CLI-004")
        )
        assert _error(respuesta, "permiso", "VERIFICACION_FALLIDA")
    respuesta = verificar_identidad(contexto, "CLI-004", _dato(contexto, "CLI-004"))
    assert _error(respuesta, "negocio", "INTENTOS_AGOTADOS")
    assert "analista" in respuesta["error"]["mensaje"]


def test_exito_reinicia_el_contador(contexto):
    incorrecto, correcto = _incorrecto(contexto, "CLI-001"), _dato(contexto, "CLI-001")
    for _ in range(2):
        verificar_identidad(contexto, "CLI-001", incorrecto)
    assert verificar_identidad(contexto, "CLI-001", correcto)["ok"] is True
    for _ in range(2):
        verificar_identidad(contexto, "CLI-001", incorrecto)
    assert verificar_identidad(contexto, "CLI-001", correcto)["ok"] is True


def test_fallos_de_un_cliente_no_afectan_a_otro(contexto):
    for _ in range(3):
        verificar_identidad(contexto, "CLI-001", _incorrecto(contexto, "CLI-001"))
    respuesta = verificar_identidad(contexto, "CLI-002", _dato(contexto, "CLI-002"))
    assert respuesta["ok"] is True


def test_cliente_inexistente_no_suma_intentos(contexto):
    for _ in range(5):
        verificar_identidad(contexto, "CLI-999", "1234")
    assert not contexto.intentos.agotados("CLI-999")


# --- registro con inyección de fallas ---


def _servidor_con_fallas(configuracion: str) -> tuple[FastMCP, Contexto]:
    contexto = Contexto(Repositorio(hoy=HOY), InyectorFallas(configuracion))
    servidor = FastMCP("prueba")
    registrar(servidor, contexto)
    return servidor, contexto


def _llamar(servidor: FastMCP, nombre: str, argumentos: dict) -> dict:
    (contenido,) = asyncio.run(servidor.call_tool(nombre, argumentos))
    return json.loads(contenido.text)


def test_buscar_respeta_la_falla_inyectada_y_luego_responde():
    servidor, _ = _servidor_con_fallas("buscar_cliente:1")
    primera = _llamar(servidor, "buscar_cliente", {"documento": "CC-FIC-0001"})
    assert primera["ok"] is False
    assert primera["error"]["tipo"] == "transitorio"
    assert primera["error"]["reintentable"] is True
    segunda = _llamar(servidor, "buscar_cliente", {"documento": "CC-FIC-0001"})
    assert _ids(segunda) == ["CLI-001"]


def test_falla_inyectada_en_verificar_no_cuenta_como_intento():
    servidor, contexto = _servidor_con_fallas("verificar_identidad:1")
    argumentos = {
        "cliente_id": "CLI-001",
        "dato_verificacion": _incorrecto(contexto, "CLI-001"),
    }
    assert _llamar(servidor, "verificar_identidad", argumentos)["error"]["tipo"] == (
        "transitorio"
    )
    for _ in range(2):
        _llamar(servidor, "verificar_identidad", argumentos)
    assert not contexto.intentos.agotados("CLI-001")
