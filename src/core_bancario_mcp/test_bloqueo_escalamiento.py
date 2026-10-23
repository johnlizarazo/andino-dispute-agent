from datetime import date

import pytest

from core_bancario_mcp.bloqueo_escalamiento import bloquear_tarjeta
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
