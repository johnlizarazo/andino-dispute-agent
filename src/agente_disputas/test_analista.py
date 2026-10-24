import json
from dataclasses import replace

import pytest

from agente_disputas.analista import (
    NOMBRE,
    definir_analista,
    leer_contexto,
    pesos,
    prompt_analista,
)
from core_bancario_mcp.repositorio import Repositorio

CONSULTAR = "mcp__core-bancario__consultar_transacciones"
VALIDO = {
    "cliente_id": " CLI-001 ",
    "ultimos4": "4821",
    "fecha_desde": "2026-10-22",
    "fecha_hasta": "2026-10-22",
    "montos_reportados": [180000],
}


@pytest.fixture
def politica():
    return Repositorio().politica


def _prompt(contexto) -> str:
    texto = contexto if isinstance(contexto, str) else json.dumps(contexto)
    return f"Analiza estos cobros.\n<contexto>{texto}</contexto>\nGracias."


def test_nombre_del_subagente():
    assert NOMBRE == "analista-transacciones"


def test_pesos_con_punto_de_miles():
    assert pesos(500000) == "$500.000"
    assert pesos(1250000) == "$1.250.000"


def test_definicion_con_una_sola_herramienta_y_resultado_dentro_del_turno(politica):
    definicion = definir_analista(politica)
    assert definicion.tools == [CONSULTAR]
    assert definicion.model == "inherit"
    assert definicion.maxTurns == 8
    assert definicion.background is False
    assert definicion.description.strip()
    assert definicion.prompt == prompt_analista(politica)


def test_prompt_usa_la_politica_vigente(politica):
    prompt = prompt_analista(politica)
    for texto in (
        "$500.000",
        "90",
        "120",
        "<contexto>",
        "<analisis>",
        "disputable",
        "sobre_umbral",
        "fuera_de_politica",
        "montos_no_encontrados",
    ):
        assert texto in prompt


def test_prompt_cambia_con_el_umbral(politica):
    prompt = prompt_analista(replace(politica, umbral_disputa_automatica=300000))
    assert "$300.000" in prompt
    assert "$500.000" not in prompt


def test_contexto_valido_se_normaliza():
    contexto, invalidos = leer_contexto(_prompt(VALIDO))
    assert invalidos == []
    assert contexto["cliente_id"] == "CLI-001"
    assert contexto["ultimos4"] == "4821"
    assert contexto["montos_reportados"] == [180000]


def test_montos_reportados_vacios_es_valido():
    _, invalidos = leer_contexto(_prompt({**VALIDO, "montos_reportados": []}))
    assert invalidos == []


def test_campo_de_mas_se_ignora():
    _, invalidos = leer_contexto(_prompt({**VALIDO, "nota": "x"}))
    assert invalidos == []


@pytest.mark.parametrize(
    "prompt", ["Sin bloque", _prompt("{no es json"), _prompt("[1]")]
)
def test_sin_bloque_legible(prompt):
    assert leer_contexto(prompt) == (None, ["contexto"])


@pytest.mark.parametrize("campo", list(VALIDO))
def test_campo_faltante_se_nombra(campo):
    contexto = {k: v for k, v in VALIDO.items() if k != campo}
    _, invalidos = leer_contexto(_prompt(contexto))
    assert invalidos == [campo]


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("cliente_id", ""),
        ("cliente_id", 7),
        ("ultimos4", "48A1"),
        ("ultimos4", "482"),
        ("fecha_desde", "2026-13-01"),
        ("fecha_hasta", "22/10/2026"),
        ("fecha_hasta", "20261022"),
        ("montos_reportados", [0]),
        ("montos_reportados", [-5]),
        ("montos_reportados", [True]),
        ("montos_reportados", ["180000"]),
        ("montos_reportados", 180000),
    ],
)
def test_campo_invalido_se_nombra(campo, valor):
    _, invalidos = leer_contexto(_prompt({**VALIDO, campo: valor}))
    assert invalidos == [campo]


def test_rango_invertido_nombra_las_fechas():
    contexto = {**VALIDO, "fecha_desde": "2026-10-23", "fecha_hasta": "2026-10-22"}
    _, invalidos = leer_contexto(_prompt(contexto))
    assert invalidos == ["fecha_desde", "fecha_hasta"]


@pytest.mark.parametrize("prompt", [None, 42, ["x"]])
def test_prompt_que_no_es_texto(prompt):
    assert leer_contexto(prompt) == (None, ["contexto"])
