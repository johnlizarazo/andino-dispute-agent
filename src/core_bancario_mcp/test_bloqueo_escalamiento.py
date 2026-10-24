import asyncio
import json
from datetime import date

import pytest
from mcp.server.fastmcp import FastMCP

from core_bancario_mcp.bloqueo_escalamiento import (
    DESCRIPCION_ESCALAR,
    bloquear_tarjeta,
    escalar_a_analista,
    registrar,
)
from core_bancario_mcp.contexto import Contexto
from core_bancario_mcp.fallas import InyectorFallas
from core_bancario_mcp.repositorio import Repositorio
from core_bancario_mcp.transacciones import consultar_transacciones, iniciar_disputa

HOY = date(2026, 10, 23)
MOTIVO = "El cliente reporta cobros que no reconoce"


@pytest.fixture
def contexto() -> Contexto:
    return Contexto(Repositorio(hoy=HOY), InyectorFallas(None))


def _error(respuesta: dict, tipo: str, codigo: str) -> bool:
    return (
        respuesta["ok"] is False
        and respuesta["error"]["tipo"] == tipo
        and respuesta["error"]["codigo"] == codigo
        and respuesta["error"]["reintentable"] is False
    )


def _estado(contexto: Contexto, tarjeta_id: str) -> str:
    return contexto.bloqueos.estado_de(contexto.repositorio.tarjetas[tarjeta_id])


# --- bloquear_tarjeta ---


def test_bloquear_tarjeta_activa_la_deja_bloqueada(contexto):
    assert bloquear_tarjeta(contexto, "CLI-001", "4821", MOTIVO) == {
        "ok": True,
        "datos": {
            "ultimos4": "4821",
            "estado": "bloqueada",
            "ya_estaba_bloqueada": False,
        },
    }
    assert _estado(contexto, "TAR-001") == "bloqueada"


def test_bloquear_dos_veces_no_es_error(contexto):
    bloquear_tarjeta(contexto, "CLI-001", "4821", MOTIVO)
    respuesta = bloquear_tarjeta(contexto, "CLI-001", "4821", MOTIVO)
    assert respuesta["ok"] is True
    assert respuesta["datos"]["ya_estaba_bloqueada"] is True


def test_bloquear_tarjeta_bloqueada_en_los_datos_no_es_error(contexto):
    respuesta = bloquear_tarjeta(contexto, "CLI-004", "9012", MOTIVO)
    assert respuesta["ok"] is True
    assert respuesta["datos"]["ya_estaba_bloqueada"] is True


def test_tarjeta_ajena_y_cliente_inexistente_dan_el_mismo_error(contexto):
    ajena = bloquear_tarjeta(contexto, "CLI-002", "4821", MOTIVO)
    inexistente = bloquear_tarjeta(contexto, "CLI-999", "4821", MOTIVO)
    assert _error(ajena, "validacion", "NO_ENCONTRADO")
    assert ajena == inexistente
    assert _estado(contexto, "TAR-001") == "activa"


@pytest.mark.parametrize(
    "argumentos",
    [
        {"motivo": ""},
        {"motivo": "   "},
        {"motivo": "x" * 501},
        {"motivo": 123},
        {"ultimos4": "48a1"},
        {"cliente_id": None},
    ],
)
def test_bloqueo_con_parametros_invalidos_no_bloquea(contexto, argumentos):
    completos = {"cliente_id": "CLI-001", "ultimos4": "4821", "motivo": MOTIVO}
    respuesta = bloquear_tarjeta(contexto, **{**completos, **argumentos})
    assert _error(respuesta, "validacion", "PARAMETRO_INVALIDO")
    assert _estado(contexto, "TAR-001") == "activa"


def test_tarjeta_bloqueada_se_sigue_consultando_y_disputando(contexto):
    bloquear_tarjeta(contexto, "CLI-001", "4821", MOTIVO)
    assert consultar_transacciones(contexto, "CLI-001", "4821")["ok"] is True
    assert iniciar_disputa(contexto, "TRX-001", MOTIVO)["ok"] is True


# --- escalar_a_analista ---

CLAVES_RESPUESTA = {"escalamiento_id", "causa", "estado", "cantidad_transacciones"}
CAUSAS = [
    "persona_solicitada",
    "umbral",
    "fuera_de_politica",
    "intentos_agotados",
    "otra",
]


def _escalar(contexto: Contexto, **argumentos) -> dict:
    completos = {
        "causa": "umbral",
        "cliente_id": "CLI-001",
        "transacciones": ["TRX-002"],
        "acciones_realizadas": "Consulté los cobros; la disputa superó el umbral",
        "accion_recomendada": "Revisar el cobro de Electro Ficticio con el cliente",
    }
    return escalar_a_analista(contexto, **{**completos, **argumentos})


def test_escalar_por_umbral_responde_solo_lo_minimo(contexto):
    assert _escalar(contexto) == {
        "ok": True,
        "datos": {
            "escalamiento_id": "ESC-0001",
            "causa": "umbral",
            "estado": "pendiente_analista",
            "cantidad_transacciones": 1,
        },
    }
    (registro,) = contexto.escalamientos.todos()
    assert registro.cliente_nombre == contexto.repositorio.clientes["CLI-001"].nombre
    (detalle,) = registro.transacciones
    assert (detalle.transaccion_id, detalle.monto, detalle.caso_disputa) == (
        "TRX-002",
        1250000,
        None,
    )
    assert detalle.fecha == "2026-10-22"
    assert registro.total == 1250000
    assert _escalar(contexto)["datos"]["escalamiento_id"] == "ESC-0002"


@pytest.mark.parametrize(
    "argumentos",
    [
        {},
        {"causa": "persona_solicitada", "cliente_id": None, "transacciones": None},
        {"causa": "intentos_agotados", "cliente_id": "CLI-004", "transacciones": None},
    ],
)
def test_respuesta_de_exito_nunca_expone_datos_de_productos(contexto, argumentos):
    respuesta = _escalar(contexto, **argumentos)
    assert set(respuesta["datos"]) == CLAVES_RESPUESTA


def test_persona_solicitada_escala_sin_cliente_ni_transacciones(contexto):
    respuesta = _escalar(
        contexto, causa="persona_solicitada", cliente_id=None, transacciones=None
    )
    assert respuesta["ok"] is True
    assert respuesta["datos"]["cantidad_transacciones"] == 0
    (registro,) = contexto.escalamientos.todos()
    assert registro.cliente_id is None
    assert registro.cliente_nombre is None


def test_intentos_agotados_exige_cliente_pero_no_transacciones(contexto):
    con_cliente = _escalar(
        contexto, causa="intentos_agotados", cliente_id="CLI-004", transacciones=None
    )
    sin_cliente = _escalar(
        contexto, causa="intentos_agotados", cliente_id=None, transacciones=None
    )
    assert con_cliente["ok"] is True
    assert _error(sin_cliente, "validacion", "PARAMETRO_INVALIDO")


def test_faltantes_se_nombran_todos_en_un_solo_error(contexto):
    respuesta = _escalar(contexto, causa=None, accion_recomendada="  ")
    assert _error(respuesta, "validacion", "PARAMETRO_INVALIDO")
    assert "causa" in respuesta["error"]["mensaje"]
    assert "accion_recomendada" in respuesta["error"]["mensaje"]


def test_causa_desconocida_lista_las_validas(contexto):
    respuesta = _escalar(contexto, causa="urgente")
    assert _error(respuesta, "validacion", "PARAMETRO_INVALIDO")
    assert all(causa in respuesta["error"]["mensaje"] for causa in CAUSAS)


@pytest.mark.parametrize("causa", ["umbral", "fuera_de_politica"])
@pytest.mark.parametrize("transacciones", [None, []])
def test_umbral_y_politica_exigen_transacciones(contexto, causa, transacciones):
    respuesta = _escalar(contexto, causa=causa, transacciones=transacciones)
    assert _error(respuesta, "validacion", "PARAMETRO_INVALIDO")


def test_transaccion_inexistente_o_ajena_dan_la_misma_respuesta(contexto):
    inexistente = _escalar(contexto, transacciones=["TRX-999"])
    ajena = _escalar(contexto, transacciones=["TRX-004"])
    assert _error(inexistente, "validacion", "NO_ENCONTRADO")
    assert ajena == inexistente  # no permite sondear qué ids existen
    assert _error(
        _escalar(contexto, cliente_id="CLI-999"), "validacion", "NO_ENCONTRADO"
    )


def test_persona_solicitada_sin_cliente_rechaza_transacciones(contexto):
    existente, inexistente = (
        _escalar(
            contexto,
            causa="persona_solicitada",
            cliente_id=None,
            transacciones=[transaccion],
        )
        for transaccion in ("TRX-001", "TRX-999")
    )
    assert _error(existente, "validacion", "PARAMETRO_INVALIDO")
    assert existente == inexistente  # sin cliente no se puede sondear qué ids existen
    assert contexto.escalamientos.todos() == []


def test_transacciones_repetidas_se_cuentan_una_vez(contexto):
    respuesta = _escalar(contexto, transacciones=["TRX-002", " TRX-002 "])
    assert respuesta["datos"]["cantidad_transacciones"] == 1
    assert contexto.escalamientos.todos()[0].total == 1250000


def test_registro_guarda_el_caso_de_disputa(contexto):
    transaccion = contexto.repositorio.obtener_transaccion("TRX-001")
    caso = contexto.disputas.abrir(transaccion, "No lo reconoce")
    _escalar(contexto, causa="otra", transacciones=["TRX-001"])
    (registro,) = contexto.escalamientos.todos()
    assert registro.transacciones[0].caso_disputa == caso.id


def test_lista_como_texto_json_se_acepta(contexto):
    respuesta = _escalar(contexto, transacciones='["TRX-002"]')
    assert respuesta["ok"] is True
    assert respuesta["datos"]["cantidad_transacciones"] == 1


@pytest.mark.parametrize("transacciones", ["TRX-002", 5, {"a": 1}, [1], '{"a": 1}'])
def test_transacciones_de_tipo_incorrecto_son_validacion(contexto, transacciones):
    respuesta = _escalar(contexto, transacciones=transacciones)
    assert _error(respuesta, "validacion", "PARAMETRO_INVALIDO")


@pytest.mark.parametrize(
    "argumentos",
    [
        {"acciones_realizadas": "x" * 1001},
        {"accion_recomendada": "x" * 501},
        {"causa": 3},
        {"cliente_id": ["CLI-001"]},
    ],
)
def test_largos_y_tipos_invalidos_son_validacion(contexto, argumentos):
    assert _error(_escalar(contexto, **argumentos), "validacion", "PARAMETRO_INVALIDO")


@pytest.mark.parametrize(
    "argumentos",
    [
        {"causa": "urgente"},
        {"causa": None},
        {"transacciones": ["TRX-999"]},
        {"transacciones": ["TRX-004"]},
        {"cliente_id": "CLI-999"},
        {"transacciones": 5},
    ],
)
def test_ningun_error_registra_el_escalamiento(contexto, argumentos):
    assert _escalar(contexto, **argumentos)["ok"] is False
    assert contexto.escalamientos.todos() == []


# --- registro con inyección de fallas ---


def _servidor_con_fallas(configuracion: str) -> tuple[FastMCP, Contexto]:
    contexto = Contexto(Repositorio(hoy=HOY), InyectorFallas(configuracion))
    servidor = FastMCP("prueba")
    registrar(servidor, contexto)
    return servidor, contexto


def _llamar(servidor: FastMCP, nombre: str, argumentos: dict) -> dict:
    (contenido,) = asyncio.run(servidor.call_tool(nombre, argumentos))
    return json.loads(contenido.text)


def test_falla_inyectada_en_bloqueo_no_bloquea():
    servidor, contexto = _servidor_con_fallas("bloquear_tarjeta:1")
    argumentos = {"cliente_id": "CLI-001", "ultimos4": "4821", "motivo": MOTIVO}
    primera = _llamar(servidor, "bloquear_tarjeta", argumentos)
    assert primera["error"]["tipo"] == "transitorio"
    assert primera["error"]["reintentable"] is True
    assert _estado(contexto, "TAR-001") == "activa"
    assert _llamar(servidor, "bloquear_tarjeta", argumentos)["ok"] is True
    assert _estado(contexto, "TAR-001") == "bloqueada"


def test_falla_inyectada_en_escalamiento_no_registra():
    servidor, contexto = _servidor_con_fallas("escalar_a_analista:1")
    argumentos = {
        "causa": "persona_solicitada",
        "acciones_realizadas": "Ninguna; el cliente pidió una persona",
        "accion_recomendada": "Contactar al cliente",
    }
    primera = _llamar(servidor, "escalar_a_analista", argumentos)
    assert primera["error"]["tipo"] == "transitorio"
    assert contexto.escalamientos.todos() == []
    assert _llamar(servidor, "escalar_a_analista", argumentos)["ok"] is True
    assert len(contexto.escalamientos.todos()) == 1


def test_descripcion_de_escalar_dice_cuando_usarla_y_cuando_no():
    # Regla 4: de inmediato si pide una persona; no solo por molestia ni si se puede resolver.
    assert "persona_solicitada" in DESCRIPCION_ESCALAR
    assert "de inmediato" in DESCRIPCION_ESCALAR
    assert "molest" in DESCRIPCION_ESCALAR
    assert "bajo el umbral" in DESCRIPCION_ESCALAR
