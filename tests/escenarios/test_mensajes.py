"""Los mensajes de la suite no pasan por memoria: no están en el prompt de sistema (#13)."""

import re

import pytest
from casos import MENSAJES, VENTANA, comparten_ventana, mensaje, normalizar

from agente_disputas.prompts import PROMPT_SISTEMA
from core_bancario_mcp.repositorio import Repositorio

CASOS = (
    "mensaje_de_ejemplo",
    "persona",
    "homonimos",
    "sin_identidad",
    "falla_transitoria",
    "fuera_de_politica",
)
EJEMPLOS = re.findall(r'Cliente: "([^"]+)"', PROMPT_SISTEMA)


def test_hay_un_mensaje_por_caso_obligatorio():
    assert tuple(MENSAJES) == CASOS


def test_el_prompt_trae_ejemplos_para_comparar():
    assert len(EJEMPLOS) >= 3


@pytest.mark.parametrize("caso", CASOS)
def test_ningun_mensaje_contiene_un_ejemplo_ni_esta_en_el_prompt(caso):
    texto = normalizar(mensaje(caso))
    assert texto not in normalizar(PROMPT_SISTEMA)
    for ejemplo in EJEMPLOS:
        assert normalizar(ejemplo) not in texto


@pytest.mark.parametrize("caso", CASOS)
def test_ningun_mensaje_comparte_ocho_palabras_seguidas_con_el_prompt(caso):
    assert not comparten_ventana(mensaje(caso), PROMPT_SISTEMA)


def test_la_ventana_detecta_una_copia_parcial():
    copia = "Hola. " + EJEMPLOS[1] + " Gracias."
    assert VENTANA == 8
    assert comparten_ventana(copia, PROMPT_SISTEMA)
    # Menos de VENTANA palabras del ejemplo no delatan una copia (sin literales: test_prompts).
    fragmento = " ".join(EJEMPLOS[1].split()[:4])
    assert not comparten_ventana(fragmento, PROMPT_SISTEMA)


def test_normalizar_quita_tildes_signos_y_espacios():
    assert normalizar("  ¡Bloquéen  la TARJETA, ya!  ") == "bloqueen la tarjeta ya"


def test_los_datos_de_verificacion_se_leen_del_core():
    clientes = Repositorio().clientes
    assert clientes["CLI-001"].dato_verificacion in mensaje("mensaje_de_ejemplo")
    assert clientes["CLI-004"].dato_verificacion in mensaje("fuera_de_politica")
    datos = {c.dato_verificacion for c in clientes.values()}
    for plantilla in MENSAJES.values():
        assert not any(dato in plantilla for dato in datos)


def test_el_caso_de_homonimos_usa_el_nombre_compartido_de_los_datos():
    clientes = Repositorio().clientes
    nombre = clientes["CLI-002"].nombre
    assert clientes["CLI-003"].nombre == nombre
    assert nombre in mensaje("homonimos")


def test_los_casos_sin_dato_quedan_igual():
    for caso in ("persona", "sin_identidad", "falla_transitoria"):
        assert mensaje(caso) == MENSAJES[caso]
