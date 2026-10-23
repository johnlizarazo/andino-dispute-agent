import json
import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest

from core_bancario_mcp.contexto import Contexto
from core_bancario_mcp.fallas import InyectorFallas
from core_bancario_mcp.repositorio import Repositorio
from core_bancario_mcp.transacciones import consultar_transacciones, iniciar_disputa

DATOS = Path(__file__).with_name("datos")
HOY = date(2026, 10, 23)
CLAVES_COBRO = {"transaccion_id", "fecha", "monto", "comercio", "pais", "caso_disputa"}


@pytest.fixture
def contexto() -> Contexto:
    return Contexto(Repositorio(hoy=HOY), InyectorFallas(None))


def _contexto_con(tmp_path: Path, cambios: dict[str, dict]) -> Contexto:
    """Copia los datos y aplica ``cambios`` por id de transacción."""
    carpeta = tmp_path / "datos"
    shutil.copytree(DATOS, carpeta)
    ruta = carpeta / "transacciones.json"
    transacciones = json.loads(ruta.read_text(encoding="utf-8"))
    for transaccion in transacciones:
        transaccion.update(cambios.get(transaccion["id"], {}))
    ruta.write_text(json.dumps(transacciones, ensure_ascii=False), encoding="utf-8")
    return Contexto(Repositorio(hoy=HOY, carpeta=carpeta), InyectorFallas(None))


def _ids(respuesta: dict) -> list[str]:
    assert respuesta["ok"] is True, respuesta
    return [c["transaccion_id"] for c in respuesta["datos"]]


def _error(respuesta: dict, tipo: str, codigo: str) -> bool:
    return (
        respuesta["ok"] is False
        and respuesta["error"]["tipo"] == tipo
        and respuesta["error"]["codigo"] == codigo
        and respuesta["error"]["reintentable"] is False
    )


# --- consultar_transacciones ---


@pytest.mark.parametrize("hoy", [date(2027, 1, 1), date(2026, 3, 1), date(2026, 11, 1)])
def test_consultar_cobros_de_ayer_del_mensaje_de_ejemplo(hoy):
    contexto = Contexto(Repositorio(hoy=hoy), InyectorFallas(None))
    ayer = (hoy - timedelta(days=1)).isoformat()
    respuesta = consultar_transacciones(contexto, "CLI-001", "4821", ayer, ayer)
    assert _ids(respuesta) == ["TRX-001", "TRX-002"]
    assert sorted(c["monto"] for c in respuesta["datos"]) == [180000, 1250000]


def test_consultar_sin_rango_usa_30_dias_ordenados_del_mas_reciente(contexto):
    assert _ids(consultar_transacciones(contexto, "CLI-001", "4821")) == [
        "TRX-001",
        "TRX-002",
        "TRX-003",
    ]


@pytest.mark.parametrize(("dias", "incluido"), [(29, True), (30, False)])
def test_rango_por_omision_cuenta_hoy_y_29_dias_atras(tmp_path, dias, incluido):
    contexto = _contexto_con(tmp_path, {"TRX-003": {"dias_atras": dias}})
    ids = _ids(consultar_transacciones(contexto, "CLI-001", "4821"))
    assert ("TRX-003" in ids) is incluido


def test_solo_fecha_desde_completa_hasta_con_hoy(contexto):
    desde = (HOY - timedelta(days=5)).isoformat()
    assert _ids(consultar_transacciones(contexto, "CLI-001", "4821", desde)) == [
        "TRX-001",
        "TRX-002",
    ]


def test_solo_fecha_hasta_completa_desde_29_dias_antes(contexto):
    hasta = (HOY - timedelta(days=2)).isoformat()
    respuesta = consultar_transacciones(contexto, "CLI-001", "4821", None, hasta)
    assert _ids(respuesta) == ["TRX-003"]


def test_rango_sin_cobros_es_exito_con_lista_vacia(contexto):
    dia = (HOY - timedelta(days=3)).isoformat()
    assert consultar_transacciones(contexto, "CLI-001", "4821", dia, dia) == {
        "ok": True,
        "datos": [],
    }


def test_tarjeta_bloqueada_tambien_lista_sus_cobros(contexto):
    assert _ids(consultar_transacciones(contexto, "CLI-004", "9012")) == ["TRX-007"]


@pytest.mark.parametrize(
    "argumentos",
    [
        {"fecha_desde": "20261023"},
        {"fecha_desde": "2026-W43-5"},
        {"fecha_desde": "2026-02-30"},
        {"fecha_desde": "2026-10-20", "fecha_hasta": "2026-10-10"},
        {"fecha_hasta": (HOY + timedelta(days=1)).isoformat()},
        {
            "fecha_desde": (HOY - timedelta(days=366)).isoformat(),
            "fecha_hasta": HOY.isoformat(),
        },
        {"fecha_desde": 20261023},
        {"ultimos4": "48a1"},
        {"cliente_id": ""},
        {"cliente_id": 1},
    ],
)
def test_parametros_invalidos_son_validacion(contexto, argumentos):
    completos = {"cliente_id": "CLI-001", "ultimos4": "4821", **argumentos}
    respuesta = consultar_transacciones(contexto, **completos)
    assert _error(respuesta, "validacion", "PARAMETRO_INVALIDO")


def test_rango_de_365_dias_es_valido(contexto):
    desde = (HOY - timedelta(days=365)).isoformat()
    respuesta = consultar_transacciones(contexto, "CLI-001", "4821", desde)
    assert respuesta["ok"] is True


def test_tarjeta_ajena_y_cliente_inexistente_dan_el_mismo_error(contexto):
    ajena = consultar_transacciones(contexto, "CLI-002", "4821")
    inexistente = consultar_transacciones(contexto, "CLI-999", "4821")
    assert _error(ajena, "validacion", "NO_ENCONTRADO")
    assert ajena == inexistente


def test_cobro_expone_solo_las_claves_del_contrato(contexto):
    respuesta = consultar_transacciones(contexto, "CLI-001", "4821")
    for cobro in respuesta["datos"]:
        assert set(cobro) == CLAVES_COBRO
        assert date.fromisoformat(cobro["fecha"])
        assert cobro["caso_disputa"] is None


def test_cobro_con_disputa_muestra_su_caso(contexto):
    transaccion = contexto.repositorio.obtener_transaccion("TRX-001")
    caso = contexto.disputas.abrir(transaccion, "No lo reconozco")
    respuesta = consultar_transacciones(contexto, "CLI-001", "4821")
    casos = {c["transaccion_id"]: c["caso_disputa"] for c in respuesta["datos"]}
    assert casos["TRX-001"] == caso.id
    assert casos["TRX-002"] is None


# --- iniciar_disputa: caso feliz y validaciones ---

MOTIVO = "El cliente no reconoce el cobro"


def test_disputa_abre_caso_con_el_monto_del_core(contexto):
    assert iniciar_disputa(contexto, "TRX-001", MOTIVO) == {
        "ok": True,
        "datos": {
            "caso_id": "CASO-0001",
            "transaccion_id": "TRX-001",
            "monto": 180000,
            "estado": "abierta",
        },
    }
    segunda = iniciar_disputa(contexto, "TRX-003", MOTIVO)
    assert segunda["datos"]["caso_id"] == "CASO-0002"


@pytest.mark.parametrize("transaccion_id", ["TRX-004", "TRX-007"])
def test_disputa_en_el_umbral_y_en_tarjeta_bloqueada_se_abre(contexto, transaccion_id):
    respuesta = iniciar_disputa(contexto, transaccion_id, MOTIVO)
    assert respuesta["ok"] is True
    assert respuesta["datos"]["transaccion_id"] == transaccion_id


def test_disputa_repetida_informa_el_caso_existente(contexto):
    iniciar_disputa(contexto, "TRX-001", MOTIVO)
    respuesta = iniciar_disputa(contexto, "TRX-001", MOTIVO)
    assert _error(respuesta, "negocio", "DISPUTA_EXISTENTE")
    assert "CASO-0001" in respuesta["error"]["mensaje"]


def test_disputa_de_transaccion_inexistente_es_validacion(contexto):
    respuesta = iniciar_disputa(contexto, "TRX-999", MOTIVO)
    assert _error(respuesta, "validacion", "NO_ENCONTRADO")


@pytest.mark.parametrize(
    "argumentos",
    [
        {"motivo": MOTIVO},
        {"transaccion_id": "TRX-001"},
        {"transaccion_id": "TRX-001", "motivo": ""},
        {"transaccion_id": "TRX-001", "motivo": "   "},
        {"transaccion_id": "TRX-001", "motivo": "x" * 501},
        {"transaccion_id": "TRX-001", "motivo": 123},
        {"transaccion_id": 1, "motivo": MOTIVO},
    ],
)
def test_disputa_con_parametros_invalidos_es_validacion(contexto, argumentos):
    respuesta = iniciar_disputa(contexto, **argumentos)
    assert _error(respuesta, "validacion", "PARAMETRO_INVALIDO")
    assert contexto.disputas.caso_de("TRX-001") is None


# --- iniciar_disputa: rechazos por política y por umbral ---


def test_politica_rechaza_cobro_en_el_exterior_de_120_dias(contexto):
    respuesta = iniciar_disputa(contexto, "TRX-006", MOTIVO)
    assert _error(respuesta, "negocio", "FUERA_DE_POLITICA")
    assert "analista" in respuesta["error"]["mensaje"]
    assert contexto.disputas.caso_de("TRX-006") is None


def test_umbral_rechaza_cobro_de_1250000_sin_abrir_caso(contexto):
    respuesta = iniciar_disputa(contexto, "TRX-002", MOTIVO)
    assert _error(respuesta, "negocio", "REQUIERE_ANALISTA")
    assert "analista" in respuesta["error"]["mensaje"]
    assert contexto.disputas.caso_de("TRX-002") is None
    cobros = consultar_transacciones(contexto, "CLI-001", "4821")["datos"]
    assert {c["transaccion_id"]: c["caso_disputa"] for c in cobros}["TRX-002"] is None


@pytest.mark.parametrize(
    ("transaccion_id", "dias", "se_abre"),
    [
        ("TRX-006", 90, True),  # exterior en el límite
        ("TRX-006", 91, False),
        ("TRX-003", 120, True),  # nacional en el límite
        ("TRX-003", 121, False),
    ],
)
def test_bordes_de_la_politica(tmp_path, transaccion_id, dias, se_abre):
    contexto = _contexto_con(tmp_path, {transaccion_id: {"dias_atras": dias}})
    respuesta = iniciar_disputa(contexto, transaccion_id, MOTIVO)
    if se_abre:
        assert respuesta["ok"] is True
    else:
        assert _error(respuesta, "negocio", "FUERA_DE_POLITICA")


def test_fuera_de_politica_y_sobre_el_umbral_responde_politica(tmp_path):
    contexto = _contexto_con(tmp_path, {"TRX-002": {"dias_atras": 121}})
    respuesta = iniciar_disputa(contexto, "TRX-002", MOTIVO)
    assert _error(respuesta, "negocio", "FUERA_DE_POLITICA")
