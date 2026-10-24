from pathlib import Path

from agente_disputas import prompts
from agente_disputas.prompts import PROMPT_SISTEMA, VERSION_PROMPT

HERRAMIENTAS = [
    "buscar_cliente",
    "verificar_identidad",
    "consultar_transacciones",
    "iniciar_disputa",
    "bloquear_tarjeta",
    "escalar_a_analista",
]


def test_prompt_menciona_las_seis_herramientas():
    assert all(herramienta in PROMPT_SISTEMA for herramienta in HERRAMIENTAS)


def test_prompt_incluye_el_umbral_y_el_manejo_de_errores():
    assert "$500.000" in PROMPT_SISTEMA
    assert "reintentable" in PROMPT_SISTEMA
    assert "dos veces" in PROMPT_SISTEMA


def test_prompt_tiene_version():
    assert VERSION_PROMPT.strip()


def test_version_3_con_las_seis_herramientas_disponibles():
    # Desde el #9 los hooks garantizan las reglas 1 y 2; ya no hay herramientas limitadas.
    assert VERSION_PROMPT == "3"
    assert "Disponibilidad actual" not in PROMPT_SISTEMA


def test_prompt_orienta_que_hacer_cuando_una_operacion_se_niega():
    assert "se niega" in PROMPT_SISTEMA


def test_ninguna_linea_del_modulo_supera_95_caracteres():
    lineas = Path(prompts.__file__).read_text(encoding="utf-8").splitlines()
    assert [n for n, linea in enumerate(lineas, 1) if len(linea) > 95] == []
