import ast
import json
import re
from importlib import resources
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


def test_version_5_sin_disponibilidad_limitada():
    assert VERSION_PROMPT == "5"
    assert "Disponibilidad actual" not in PROMPT_SISTEMA


def test_prompt_orienta_la_delegacion_con_el_contexto_explicito():
    assert "analista-transacciones" in PROMPT_SISTEMA
    assert "<contexto>" in PROMPT_SISTEMA
    for campo in (
        "cliente_id",
        "ultimos4",
        "fecha_desde",
        "fecha_hasta",
        "montos_reportados",
    ):
        assert campo in PROMPT_SISTEMA


def test_prompt_orienta_que_hacer_cuando_una_operacion_se_niega():
    assert "se niega" in PROMPT_SISTEMA


def test_ninguna_linea_del_modulo_supera_95_caracteres():
    lineas = Path(prompts.__file__).read_text(encoding="utf-8").splitlines()
    assert [n for n, linea in enumerate(lineas, 1) if len(linea) > 95] == []


def _ejemplos() -> str:
    (bloque,) = re.findall(r"<ejemplos>(.*?)</ejemplos>", PROMPT_SISTEMA, re.DOTALL)
    return bloque


def test_entre_tres_y_cinco_ejemplos_con_la_accion_esperada():
    assert 3 <= _ejemplos().count("Acción esperada:") <= 5
    assert _ejemplos().count("Cliente:") == _ejemplos().count("Acción esperada:")


def test_prompt_orienta_persona_a_pedido_politica_y_molestia():
    for texto in (
        "persona_solicitada",
        "fuera_de_politica",
        "molest",
        "Varios asuntos",
    ):
        assert texto in PROMPT_SISTEMA


def _leer_datos(archivo: str) -> list[dict]:
    datos = resources.files("core_bancario_mcp") / "datos"
    return json.loads((datos / archivo).read_text(encoding="utf-8"))


def _datos_del_core() -> set[str]:
    prohibidos = set()
    for cliente in _leer_datos("clientes.json"):
        prohibidos |= {cliente["id"], cliente["documento"]}
    for tarjeta in _leer_datos("tarjetas.json"):
        prohibidos |= {tarjeta["id"], tarjeta["ultimos4"]}
    for transaccion in _leer_datos("transacciones.json"):
        monto = transaccion["monto"]
        prohibidos |= {transaccion["id"], str(monto), f"{monto:,}".replace(",", ".")}
    return prohibidos


def _mensajes_de_escenarios() -> set[str]:
    raiz = Path(__file__).parents[2] / "tests" / "escenarios"
    textos = set()
    for archivo in raiz.glob("*.py"):
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
            if (
                isinstance(nodo, ast.Constant)
                and isinstance(nodo.value, str)
                and len(nodo.value) > 20
            ):
                textos.add(nodo.value)
    return textos


def _aparece(dato: str, texto: str) -> bool:
    """El dato como número o palabra completa (4821 no coincide con 48210 ni con 1.4821)."""
    patron = r"(?<!\w)(?<!\d\.)" + re.escape(dato) + r"(?!\w)(?!\.\d)"
    return re.search(patron, texto) is not None


def test_la_deteccion_de_datos_funciona():
    assert _aparece("4821", "tarjeta 4821.")
    assert _aparece("1.250.000", "un cobro de $1.250.000 ayer")
    assert not _aparece("4821", "48210")
    assert not _aparece("250.000", "$1.250.000")


def test_ejemplos_no_comparten_datos_con_el_core_ni_con_los_escenarios():
    # Principio VI: un escenario no debe poder pasar por memoria de un ejemplo.
    ejemplos = _ejemplos()
    assert _mensajes_de_escenarios(), "no se encontraron mensajes de escenario"
    assert [d for d in _datos_del_core() if _aparece(d, ejemplos)] == []
    assert [m for m in _mensajes_de_escenarios() if m in ejemplos] == []
