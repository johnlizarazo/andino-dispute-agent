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


# --- escalamiento pendiente: estado (#10) ---


def test_estado_nace_sin_pendientes():
    estado = EstadoSesion()
    assert estado.pendientes == {}
    assert estado.cierres_impedidos == 0


def test_negacion_por_umbral_crea_un_pendiente(controles):
    _verificar(controles, _exito("CLI-001"))
    _negada(_disputar(controles, "TRX-002"))
    _negada(_disputar(controles, " TRX-002 "))
    assert controles.estado.pendientes == {"TRX-002": "umbral"}


def test_otras_negaciones_no_crean_pendientes(controles, repositorio):
    _negada(_disputar(controles, "TRX-002"))  # SIN_IDENTIDAD
    _verificar(controles, _exito("CLI-001"))
    _negada(_antes(controles, CONSULTAR, {"cliente_id": "CLI-002", "ultimos4": "1357"}))
    _negada(_disputar(controles, "TRX-004"))  # TRANSACCION_NO_CONFIRMADA
    _negada(_antes(controles, "mcp__core-bancario__otra", {}))  # FALLA_CONTROL
    assert controles.estado.pendientes == {}


# --- escalamiento pendiente: creación por el core, Stop, limpieza (US1) ---

ESCALAR = "mcp__core-bancario__escalar_a_analista"


def _error_core(codigo: str) -> dict:
    return {
        "ok": False,
        "error": {
            "tipo": "negocio",
            "codigo": codigo,
            "mensaje": "Mensaje del core.",
            "reintentable": False,
        },
    }


def _bloques(respuesta: dict) -> list:
    """Forma real de tool_response para herramientas MCP (verificada con la API en el #9)."""
    return [{"type": "text", "text": json.dumps(respuesta)}]


def _despues_de_disputar(controles: Controles, transaccion_id, respuesta) -> dict:
    entrada = {
        "hook_event_name": "PostToolUse",
        "tool_name": DISPUTAR,
        "tool_input": {"transaccion_id": transaccion_id, "motivo": "x"},
        "tool_response": respuesta,
    }
    return asyncio.run(controles.despues_de_disputar(entrada, "uso-3", {}))


def _escalar(controles: Controles, respuesta, causa="umbral", transacciones=None):
    entrada = {
        "hook_event_name": "PostToolUse",
        "tool_name": ESCALAR,
        "tool_input": {
            "causa": causa,
            "cliente_id": "CLI-001",
            "transacciones": ["TRX-002"] if transacciones is None else transacciones,
            "acciones_realizadas": "Disputa negada por umbral",
            "accion_recomendada": "Revisar el cobro",
        },
        "tool_response": respuesta,
    }
    return asyncio.run(controles.despues_de_escalar(entrada, "uso-4", {}))


ESCALADO = {
    "ok": True,
    "datos": {
        "escalamiento_id": "ESC-0001",
        "causa": "umbral",
        "estado": "pendiente",
        "cantidad_transacciones": 1,
    },
}


def _terminar(controles: Controles) -> dict:
    entrada = {"hook_event_name": "Stop", "stop_hook_active": False}
    return asyncio.run(controles.antes_de_terminar(entrada, None, {}))


def _nuevo_mensaje(controles: Controles) -> dict:
    entrada = {"hook_event_name": "UserPromptSubmit", "prompt": "Hola"}
    return asyncio.run(controles.al_recibir_mensaje(entrada, None, {}))


@pytest.mark.parametrize(
    ("codigo", "causa"),
    [("FUERA_DE_POLITICA", "fuera_de_politica"), ("REQUIERE_ANALISTA", "umbral")],
)
def test_rechazo_del_core_crea_pendiente(controles, codigo, causa):
    assert (
        _despues_de_disputar(controles, " TRX-006 ", _bloques(_error_core(codigo)))
        == {}
    )
    assert controles.estado.pendientes == {"TRX-006": causa}


@pytest.mark.parametrize(
    "respuesta",
    [
        _bloques({"ok": True, "datos": {"caso_id": "CASO-0001"}}),
        _bloques(_error_core("DISPUTA_EXISTENTE")),
        "ilegible",
        None,
    ],
)
def test_otras_respuestas_de_disputa_no_crean_pendiente(controles, respuesta):
    assert _despues_de_disputar(controles, "TRX-006", respuesta) == {}
    assert controles.estado.pendientes == {}


def test_disputa_sin_transaccion_no_crea_pendiente(controles):
    _despues_de_disputar(controles, None, _bloques(_error_core("FUERA_DE_POLITICA")))
    assert controles.estado.pendientes == {}


def test_sin_pendientes_el_turno_termina(controles):
    assert _terminar(controles) == {}
    assert controles.estado.cierres_impedidos == 0


def test_con_pendiente_se_impide_terminar_hasta_el_tope(controles):
    controles.estado.pendientes["TRX-002"] = "umbral"
    for _ in range(2):
        salida = _terminar(controles)
        assert salida["decision"] == "block"
        assert "TRX-002" in salida["reason"]
        assert "umbral" in salida["reason"]
        assert "escalar_a_analista" in salida["reason"]
        assert "1.250.000" not in salida["reason"]
    assert _terminar(controles) == {}  # tope alcanzado: deja terminar
    assert controles.estado.pendientes == {"TRX-002": "umbral"}
    assert controles.estado.cierres_impedidos == 2


@pytest.mark.parametrize("transacciones", [["TRX-002"], '["TRX-002"]', [" TRX-002 "]])
def test_escalamiento_exitoso_con_la_transaccion_limpia(controles, transacciones):
    controles.estado.pendientes["TRX-002"] = "umbral"
    assert _escalar(controles, _bloques(ESCALADO), transacciones=transacciones) == {}
    assert controles.estado.pendientes == {}
    assert _terminar(controles) == {}


@pytest.mark.parametrize(
    ("respuesta", "causa", "transacciones"),
    [
        (_bloques(ESCALADO), "umbral", ["TRX-001"]),
        (_bloques(ESCALADO), "otra", ["TRX-002"]),
        (_bloques(_error_core("FALLA_TRANSITORIA")), "umbral", ["TRX-002"]),
        ("ilegible", "umbral", ["TRX-002"]),
        (_bloques(ESCALADO), "umbral", "no es una lista"),
    ],
)
def test_escalamiento_que_no_cubre_el_pendiente_no_limpia(
    controles, respuesta, causa, transacciones
):
    controles.estado.pendientes["TRX-002"] = "umbral"
    _escalar(controles, respuesta, causa=causa, transacciones=transacciones)
    assert controles.estado.pendientes == {"TRX-002": "umbral"}


def test_escalar_una_de_dos_deja_la_otra(controles):
    controles.estado.pendientes.update(
        {"TRX-002": "umbral", "TRX-006": "fuera_de_politica"}
    )
    _escalar(controles, _bloques(ESCALADO))
    assert controles.estado.pendientes == {"TRX-006": "fuera_de_politica"}
    assert "TRX-006" in _terminar(controles)["reason"]


def test_escalamiento_por_persona_sin_cliente_no_limpia(controles):
    controles.estado.pendientes["TRX-002"] = "umbral"
    entrada = {
        "tool_name": ESCALAR,
        "tool_input": {"causa": "persona_solicitada", "acciones_realizadas": "x"},
        "tool_response": _bloques(ESCALADO),
    }
    asyncio.run(controles.despues_de_escalar(entrada, None, {}))
    assert controles.estado.pendientes == {"TRX-002": "umbral"}


def test_nuevo_mensaje_vacia_pendientes_y_reinicia_el_tope(controles):
    controles.estado.pendientes["TRX-002"] = "umbral"
    controles.estado.cierres_impedidos = 2
    assert _nuevo_mensaje(controles) == {}
    assert controles.estado.pendientes == {}
    assert controles.estado.cierres_impedidos == 0


@pytest.mark.parametrize("entrada", [None, {}, {"tool_input": "x"}])
def test_entradas_mal_formadas_no_cambian_el_estado(controles, entrada):
    controles.estado.pendientes["TRX-002"] = "umbral"
    for callback in (controles.despues_de_disputar, controles.despues_de_escalar):
        assert asyncio.run(callback(entrada, None, {})) == {}
    assert controles.estado.pendientes == {"TRX-002": "umbral"}


def test_falla_interna_del_stop_deja_terminar(controles):
    controles.estado.pendientes = None  # fuerza un error interno
    assert _terminar(controles) == {}


# --- mensaje de ejemplo (US2, FR-006) ---


def test_mensaje_de_ejemplo_el_pendiente_no_impide_lo_resoluble(controles):
    # Dos cobros de ayer en la 4821 (180.000 y 1.250.000) y el pedido de bloqueo.
    _verificar(controles, _exito("CLI-001"))
    _negada(_disputar(controles, "TRX-002"))
    assert controles.estado.pendientes == {"TRX-002": "umbral"}
    assert _disputar(controles, "TRX-001") == {}
    assert _antes(controles, BLOQUEAR, OPERACIONES[BLOQUEAR]) == {}
    assert _terminar(controles)["decision"] == "block"
    _escalar(controles, _bloques(ESCALADO))
    assert _terminar(controles) == {}


# --- heredados del #10 (#11) ---


@pytest.mark.parametrize("entrada", [None, {}])
def test_cierre_y_mensaje_nuevo_con_entrada_mal_formada_no_lanzan(controles, entrada):
    controles.estado.pendientes["TRX-002"] = "umbral"
    assert (
        asyncio.run(controles.antes_de_terminar(entrada, None, {}))["decision"]
        == "block"
    )
    assert asyncio.run(controles.al_recibir_mensaje(entrada, None, {})) == {}


def test_mensaje_de_un_subagente_no_vacia_pendientes(controles):
    controles.estado.pendientes["TRX-002"] = "umbral"
    entrada = {"hook_event_name": "UserPromptSubmit", "agent_id": "a1", "prompt": "x"}
    assert asyncio.run(controles.al_recibir_mensaje(entrada, None, {})) == {}
    assert controles.estado.pendientes == {"TRX-002": "umbral"}


# --- control de la delegación al subagente (#11) ---

DELEGAR = "Agent"
CONTEXTO = {
    "cliente_id": "CLI-001",
    "ultimos4": "4821",
    "fecha_desde": "2026-10-22",
    "fecha_hasta": "2026-10-22",
    "montos_reportados": [180000, 1250000],
}


def _prompt_delegacion(contexto) -> str:
    return f"Analiza los cobros.\n<contexto>{json.dumps(contexto)}</contexto>"


def _delegar(controles, prompt, subagente="analista-transacciones", **extra) -> dict:
    entrada = {
        "hook_event_name": "PreToolUse",
        "tool_name": DELEGAR,
        "tool_input": {
            "subagent_type": subagente,
            "description": "Analizar cobros",
            "prompt": prompt,
            **extra,
        },
    }
    return asyncio.run(controles.antes_de_delegar(entrada, "uso-5", {}))


def test_delegacion_sin_identidad_se_niega(controles):
    _negada(_delegar(controles, _prompt_delegacion(CONTEXTO)))
    assert _codigos(controles) == ["SIN_IDENTIDAD"]


def test_delegacion_valida_se_autoriza(controles):
    _verificar(controles, _exito("CLI-001"))
    assert _delegar(controles, _prompt_delegacion(CONTEXTO)) == {}
    assert (
        _delegar(controles, _prompt_delegacion(CONTEXTO), run_in_background=False) == {}
    )
    assert controles.estado.negaciones == []


def test_delegacion_a_otro_subagente_se_niega(controles):
    _verificar(controles, _exito("CLI-001"))
    _negada(
        _delegar(controles, _prompt_delegacion(CONTEXTO), subagente="general-purpose")
    )
    assert _codigos(controles) == ["SUBAGENTE_NO_PERMITIDO"]


def test_delegacion_en_segundo_plano_se_niega(controles):
    _verificar(controles, _exito("CLI-001"))
    _negada(_delegar(controles, _prompt_delegacion(CONTEXTO), run_in_background=True))
    assert _codigos(controles) == ["SEGUNDO_PLANO_NO_PERMITIDO"]


@pytest.mark.parametrize(
    ("prompt", "campo"),
    [
        ("Analiza los cobros de la 4821", "contexto"),
        (_prompt_delegacion({**CONTEXTO, "ultimos4": "48A1"}), "ultimos4"),
        (_prompt_delegacion({**CONTEXTO, "fecha_hasta": "ayer"}), "fecha_hasta"),
    ],
)
def test_delegacion_con_contexto_incompleto_nombra_el_campo(controles, prompt, campo):
    _verificar(controles, _exito("CLI-001"))
    razon = _negada(_delegar(controles, prompt))
    assert campo in razon
    assert "48A1" not in razon and "ayer" not in razon
    assert _codigos(controles) == ["CONTEXTO_INCOMPLETO"]


def test_delegacion_para_otro_cliente_se_niega_sin_revelarlo(controles):
    _verificar(controles, _exito("CLI-001"))
    razon = _negada(
        _delegar(controles, _prompt_delegacion({**CONTEXTO, "cliente_id": "CLI-002"}))
    )
    assert "CLI-002" not in razon
    assert _codigos(controles) == ["CLIENTE_DISTINTO"]


@pytest.mark.parametrize(
    "entrada",
    [
        None,
        {},
        {"tool_name": DELEGAR, "tool_input": "x"},
        {"tool_name": DELEGAR, "tool_input": {}},
    ],
)
def test_delegacion_mal_formada_nunca_se_autoriza(controles, entrada):
    _verificar(controles, _exito("CLI-001"))
    _negada(asyncio.run(controles.antes_de_delegar(entrada, None, {})))


def _consulta_del_subagente(controles, cliente_id) -> dict:
    entrada = {
        "hook_event_name": "PreToolUse",
        "tool_name": CONSULTAR,
        "tool_input": {"cliente_id": cliente_id, "ultimos4": "4821"},
        "agent_id": "sub-1",
        "agent_type": "analista-transacciones",
    }
    return asyncio.run(controles.antes_de_herramienta(entrada, "uso-6", {}))


def test_consultas_del_subagente_pasan_por_los_mismos_controles(controles):
    _verificar(controles, _exito("CLI-001"))
    assert _consulta_del_subagente(controles, "CLI-001") == {}
    _negada(_consulta_del_subagente(controles, "CLI-002"))
    assert _codigos(controles) == ["CLIENTE_DISTINTO"]


def test_la_clasificacion_no_habilita_una_disputa_sobre_el_umbral(controles):
    # Aunque el subagente hubiera marcado TRX-002 como disputable, el umbral decide (L2).
    _verificar(controles, _exito("CLI-001"))
    assert _delegar(controles, _prompt_delegacion(CONTEXTO)) == {}
    _negada(_disputar(controles, "TRX-002"))
    assert _codigos(controles) == ["REQUIERE_ANALISTA"]


# --- tool_use_id de las negaciones (#12) ---


def test_negacion_guarda_el_tool_use_id_del_hook(controles):
    _negada(_antes(controles, BLOQUEAR, OPERACIONES[BLOQUEAR]))
    _negada(_delegar(controles, _prompt_delegacion(CONTEXTO)))
    assert [n.tool_use_id for n in controles.estado.negaciones] == ["uso-2", "uso-5"]


def test_sin_argumento_usa_el_tool_use_id_de_la_entrada(controles):
    entrada = {
        "hook_event_name": "PreToolUse",
        "tool_name": BLOQUEAR,
        "tool_input": OPERACIONES[BLOQUEAR],
        "tool_use_id": "uso-entrada",
    }
    _negada(asyncio.run(controles.antes_de_herramienta(entrada, None, {})))
    assert controles.estado.negaciones[-1].tool_use_id == "uso-entrada"


def test_sin_tool_use_id_la_negacion_queda_sin_el(controles):
    entrada = {
        "hook_event_name": "PreToolUse",
        "tool_name": BLOQUEAR,
        "tool_input": OPERACIONES[BLOQUEAR],
    }
    salida = asyncio.run(controles.antes_de_herramienta(entrada, None, {}))
    assert _negada(salida) == _negada(
        _antes(controles, BLOQUEAR, OPERACIONES[BLOQUEAR])
    )
    assert controles.estado.negaciones[0].tool_use_id is None
