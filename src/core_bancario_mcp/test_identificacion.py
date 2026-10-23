import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from core_bancario_mcp.contexto import Contexto
from core_bancario_mcp.fallas import InyectorFallas
from core_bancario_mcp.identificacion import buscar_cliente
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
