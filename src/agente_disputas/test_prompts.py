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
