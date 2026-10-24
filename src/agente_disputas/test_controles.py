import asyncio
import json
from dataclasses import replace
from datetime import date

import pytest

from agente_disputas.controles import Controles, EstadoSesion, leer_respuesta
from core_bancario_mcp.repositorio import Repositorio

HOY = date(2026, 10, 23)
VERIFICAR = "mcp__core-bancario__verificar_identidad"


@pytest.fixture
def repositorio() -> Repositorio:
    return Repositorio(hoy=HOY)


@pytest.fixture
def controles(repositorio) -> Controles:
    return Controles(repositorio.obtener_transaccion, repositorio.politica)


def _exito(cliente_id: str) -> dict:
    return {"ok": True, "datos": {"cliente_id": cliente_id, "verificado": True}}


def _fallo() -> dict:
    return {
        "ok": False,
        "error": {
            "tipo": "permiso",
            "codigo": "VERIFICACION_FALLIDA",
            "mensaje": "El dato no coincide.",
            "reintentable": False,
        },
    }


def _verificar(controles: Controles, respuesta, cliente_id="CLI-001") -> dict:
    entrada = {
        "hook_event_name": "PostToolUse",
        "tool_name": VERIFICAR,
        "tool_input": {"cliente_id": cliente_id, "dato_verificacion": "0000"},
        "tool_response": respuesta,
    }
    return asyncio.run(
        controles.despues_de_verificar(entrada, "uso-1", {"signal": None})
    )


# --- leer_respuesta ---


@pytest.mark.parametrize(
    "forma",
    [
        lambda r: r,
        lambda r: {"structuredContent": r},
        lambda r: {"content": [{"type": "text", "text": json.dumps(r)}]},
        lambda r: [{"type": "text", "text": json.dumps(r)}],
        lambda r: json.dumps(r),
    ],
    ids=["contrato", "estructurado", "content", "bloques", "texto"],
)
def test_leer_respuesta_acepta_las_formas_conocidas(forma):
    assert leer_respuesta(forma(_exito("CLI-001"))) == _exito("CLI-001")


@pytest.mark.parametrize(
    "respuesta",
    [None, "x", [], 42, "{}", {"datos": {}}, [{"type": "image"}], '["ok"]'],
)
def test_leer_respuesta_rechaza_lo_demas(respuesta):
    assert leer_respuesta(respuesta) is None


# --- despues_de_verificar ---


def test_verificacion_exitosa_registra_al_cliente(controles):
    assert _verificar(controles, _exito("CLI-001"), cliente_id=" CLI-001 ") == {}
    assert controles.estado.cliente_verificado == "CLI-001"


@pytest.mark.parametrize(
    "respuesta",
    [
        _fallo(),
        None,
        "ilegible",
        {"ok": True, "datos": {"cliente_id": "CLI-001", "verificado": False}},
        {"ok": True, "datos": {"cliente_id": "", "verificado": True}},
        _exito("CLI-002"),  # el core respondió por otro cliente que el pedido
    ],
)
def test_verificacion_fallida_o_ilegible_no_registra(controles, respuesta):
    assert _verificar(controles, respuesta) == {}
    assert controles.estado.cliente_verificado is None


def test_el_ultimo_verificado_reemplaza_al_anterior(controles):
    _verificar(controles, _exito("CLI-001"))
    _verificar(controles, _exito("CLI-002"), cliente_id="CLI-002")
    assert controles.estado.cliente_verificado == "CLI-002"


def test_un_fallo_posterior_no_borra_al_verificado(controles):
    _verificar(controles, _exito("CLI-001"))
    _verificar(controles, _fallo(), cliente_id="CLI-002")
    assert controles.estado.cliente_verificado == "CLI-001"


@pytest.mark.parametrize("entrada", [{}, {"tool_input": "x"}, None])
def test_entrada_mal_formada_no_registra_ni_lanza(controles, entrada):
    respuesta = asyncio.run(controles.despues_de_verificar(entrada, None, {}))
    assert respuesta == {}
    assert controles.estado.cliente_verificado is None


def test_cada_controles_nace_sin_verificar(repositorio):
    estado = Controles(repositorio.obtener_transaccion, repositorio.politica).estado
    assert estado == EstadoSesion()
    assert estado.negaciones == []


# --- antes_de_herramienta: identidad (US1) ---

CONSULTAR = "mcp__core-bancario__consultar_transacciones"
DISPUTAR = "mcp__core-bancario__iniciar_disputa"
BLOQUEAR = "mcp__core-bancario__bloquear_tarjeta"
OPERACIONES = {
    CONSULTAR: {"cliente_id": "CLI-001", "ultimos4": "4821"},
    DISPUTAR: {"transaccion_id": "TRX-001", "motivo": "No reconozco el cobro"},
    BLOQUEAR: {"cliente_id": "CLI-001", "ultimos4": "4821", "motivo": "Sospecha"},
}


def _antes(controles: Controles, herramienta: str, tool_input) -> dict:
    entrada = {
        "hook_event_name": "PreToolUse",
        "tool_name": herramienta,
        "tool_input": tool_input,
    }
    return asyncio.run(
        controles.antes_de_herramienta(entrada, "uso-2", {"signal": None})
    )


def _negada(salida: dict) -> str:
    """Razón de la negación; falla si la salida no es una negación del PreToolUse."""
    especifica = salida["hookSpecificOutput"]
    assert especifica["hookEventName"] == "PreToolUse"
    assert especifica["permissionDecision"] == "deny"
    assert especifica["permissionDecisionReason"].strip()
    return especifica["permissionDecisionReason"]


def _codigos(controles: Controles) -> list[str]:
    return [n.codigo for n in controles.estado.negaciones]


@pytest.mark.parametrize("herramienta", list(OPERACIONES))
def test_sin_identidad_verificada_se_niega(controles, herramienta):
    razon = _negada(_antes(controles, herramienta, OPERACIONES[herramienta]))
    assert "verifica" in razon.lower()
    assert controles.estado.negaciones[-1].herramienta == herramienta
    assert _codigos(controles) == ["SIN_IDENTIDAD"]


def test_disputa_sin_identidad_verificada_se_niega_caso_del_issue(controles):
    _negada(_antes(controles, DISPUTAR, {"transaccion_id": "TRX-001", "motivo": "x"}))
    assert _codigos(controles) == ["SIN_IDENTIDAD"]


@pytest.mark.parametrize("herramienta", list(OPERACIONES))
def test_con_identidad_verificada_se_autoriza(controles, herramienta):
    _verificar(controles, _exito("CLI-001"))
    assert _antes(controles, herramienta, OPERACIONES[herramienta]) == {}
    assert controles.estado.negaciones == []


def test_una_verificacion_fallida_no_autoriza(controles):
    _verificar(controles, _fallo())
    _negada(_antes(controles, CONSULTAR, OPERACIONES[CONSULTAR]))
    assert _codigos(controles) == ["SIN_IDENTIDAD"]


def test_herramienta_inesperada_se_niega(controles):
    _verificar(controles, _exito("CLI-001"))
    _negada(_antes(controles, "mcp__core-bancario__otra", {"cliente_id": "CLI-001"}))
    assert _codigos(controles) == ["FALLA_CONTROL"]


# --- antes_de_herramienta: titularidad (US2) ---


@pytest.mark.parametrize("herramienta", [CONSULTAR, BLOQUEAR])
@pytest.mark.parametrize("cliente_id", ["CLI-002", None, 123, ["CLI-001"], ""])
def test_titular_distinto_o_mal_indicado_se_niega(controles, herramienta, cliente_id):
    _verificar(controles, _exito("CLI-001"))
    argumentos = {**OPERACIONES[herramienta], "cliente_id": cliente_id}
    razon = _negada(_antes(controles, herramienta, argumentos))
    assert "CLI-002" not in razon
    assert _codigos(controles) == ["CLIENTE_DISTINTO"]


@pytest.mark.parametrize("herramienta", [CONSULTAR, BLOQUEAR])
def test_titular_sin_cliente_id_se_niega(controles, herramienta):
    _verificar(controles, _exito("CLI-001"))
    _negada(_antes(controles, herramienta, {"ultimos4": "4821"}))
    assert _codigos(controles) == ["CLIENTE_DISTINTO"]


@pytest.mark.parametrize("herramienta", [CONSULTAR, BLOQUEAR])
def test_titular_con_espacios_se_trata_como_el_core(controles, herramienta):
    _verificar(controles, _exito("CLI-001"))
    argumentos = {**OPERACIONES[herramienta], "cliente_id": " CLI-001 "}
    assert _antes(controles, herramienta, argumentos) == {}


def _disputar(controles: Controles, transaccion_id) -> dict:
    return _antes(
        controles, DISPUTAR, {"transaccion_id": transaccion_id, "motivo": "x"}
    )


def test_disputa_de_transaccion_ajena_o_inexistente_da_la_misma_razon(controles):
    _verificar(controles, _exito("CLI-001"))
    razones = {_negada(_disputar(controles, t)) for t in ("TRX-004", "TRX-999")}
    razones.add(_negada(_antes(controles, DISPUTAR, {"motivo": "x"})))
    razones |= {_negada(_disputar(controles, t)) for t in (None, 7, ["TRX-001"])}
    assert len(razones) == 1  # no permite sondear qué ids existen ni de quién son
    assert "CLI-002" not in razones.pop()
    assert set(_codigos(controles)) == {"TRANSACCION_NO_CONFIRMADA"}


def test_titular_de_disputa_con_espacios_se_trata_como_el_core(controles):
    _verificar(controles, _exito("CLI-001"))
    assert _disputar(controles, " TRX-001 ") == {}


def test_el_titular_valido_es_el_ultimo_verificado(controles):
    _verificar(controles, _exito("CLI-001"))
    _verificar(controles, _exito("CLI-002"), cliente_id="CLI-002")
    assert _disputar(controles, "TRX-004") == {}
    _negada(_disputar(controles, "TRX-001"))
    assert _codigos(controles) == ["TRANSACCION_NO_CONFIRMADA"]


# --- antes_de_herramienta: umbral y falla cerrada (US3) ---


def test_disputa_sobre_el_umbral_se_niega_y_pide_analista(controles):
    _verificar(controles, _exito("CLI-001"))
    razon = _negada(_disputar(controles, "TRX-002"))  # 1.250.000
    assert "analista" in razon.lower()
    assert _codigos(controles) == ["REQUIERE_ANALISTA"]


def test_disputa_bajo_el_umbral_se_autoriza(controles):
    _verificar(controles, _exito("CLI-001"))
    assert _disputar(controles, "TRX-001") == {}  # 180.000


def test_disputa_de_exactamente_el_umbral_se_autoriza(controles):
    _verificar(controles, _exito("CLI-002"), cliente_id="CLI-002")
    assert _disputar(controles, "TRX-004") == {}  # 500.000, inclusive


def _verificado(controles: Controles) -> Controles:
    _verificar(controles, _exito("CLI-001"))
    return controles


def test_falla_inyectada_en_la_consulta_niega_y_luego_autoriza():
    controles = _verificado(
        Controles.desde_entorno({"CORE_BANCARIO_FALLAS": "control_transaccion:1"})
    )
    _negada(_disputar(controles, "TRX-001"))
    assert _disputar(controles, "TRX-001") == {}
    assert _codigos(controles) == ["FALLA_CONTROL"]


def test_desde_entorno_sin_fallas_usa_los_datos_del_core():
    controles = _verificado(Controles.desde_entorno({}))
    assert _disputar(controles, "TRX-001") == {}
    _negada(_disputar(controles, "TRX-002"))
    assert _codigos(controles) == ["REQUIERE_ANALISTA"]


def test_datos_que_no_cargan_niegan_toda_disputa(monkeypatch):
    from agente_disputas import controles as modulo
    from core_bancario_mcp.repositorio import DatosInvalidosError

    def repositorio_roto(*_, **__):
        raise DatosInvalidosError("datos rotos")

    monkeypatch.setattr(modulo, "Repositorio", repositorio_roto)
    controles = _verificado(Controles.desde_entorno({}))
    _negada(_disputar(controles, "TRX-001"))
    assert _codigos(controles) == ["FALLA_CONTROL"]
    # Consultar y bloquear no necesitan los datos de transacciones.
    assert _antes(controles, CONSULTAR, OPERACIONES[CONSULTAR]) == {}


def test_configuracion_de_fallas_invalida_niega_toda_disputa():
    controles = _verificado(Controles.desde_entorno({"CORE_BANCARIO_FALLAS": "mal"}))
    _negada(_disputar(controles, "TRX-001"))
    assert _codigos(controles) == ["FALLA_CONTROL"]


def test_consulta_que_lanza_niega(repositorio):
    def consulta_rota(_):
        raise RuntimeError("sin conexión")

    controles = _verificado(Controles(consulta_rota, repositorio.politica))
    _negada(_disputar(controles, "TRX-001"))
    assert _codigos(controles) == ["FALLA_CONTROL"]


def test_sin_politica_niega(repositorio):
    controles = _verificado(Controles(repositorio.obtener_transaccion, None))
    _negada(_disputar(controles, "TRX-001"))
    assert _codigos(controles) == ["FALLA_CONTROL"]


@pytest.mark.parametrize("tool_input", ["TRX-001", None, ["TRX-001"]])
def test_argumentos_que_no_son_un_objeto_niegan(controles, tool_input):
    _verificar(controles, _exito("CLI-001"))
    for herramienta in OPERACIONES:
        _negada(_antes(controles, herramienta, tool_input))
    assert set(_codigos(controles)) == {"FALLA_CONTROL"}


@pytest.mark.parametrize("entrada", [None, {}, {"tool_name": DISPUTAR}])
def test_entrada_mal_formada_niega(controles, entrada):
    salida = asyncio.run(controles.antes_de_herramienta(entrada, None, {}))
    _negada(salida)
    assert _codigos(controles) == ["FALLA_CONTROL"]
    if not isinstance(entrada, dict) or "tool_name" not in entrada:
        assert controles.estado.negaciones[-1].herramienta == "desconocida"


def test_la_razon_del_umbral_sale_de_la_politica(repositorio):
    politica = replace(repositorio.politica, umbral_disputa_automatica=300000)
    controles = _verificado(Controles(repositorio.obtener_transaccion, politica))
    razon = _negada(_disputar(controles, "TRX-002"))
    assert "$300.000" in razon
    assert "$500.000" not in razon
