import pytest

from core_bancario_mcp.fallas import (
    VARIABLE,
    ConfiguracionFallasError,
    InyectorFallas,
    con_fallas,
    desde_entorno,
)


def test_falla_n_veces_y_luego_deja_pasar():
    inyector = InyectorFallas("consultar:2")
    assert [inyector.debe_fallar("consultar") for _ in range(3)] == [True, True, False]


@pytest.mark.parametrize("configuracion", [None, "", "   "])
def test_sin_configuracion_nunca_falla(configuracion):
    inyector = InyectorFallas(configuracion)
    assert not any(inyector.debe_fallar("consultar") for _ in range(5))


def test_operaciones_independientes():
    inyector = InyectorFallas("a:1, b:2")
    assert inyector.debe_fallar("b")
    assert inyector.debe_fallar("a")
    assert not inyector.debe_fallar("a")
    assert inyector.debe_fallar("b")
    assert not inyector.debe_fallar("b")
    assert not inyector.debe_fallar("c")


@pytest.mark.parametrize(
    "invalida", ["consultar", "consultar:x", "consultar:0", "x:-1"]
)
def test_configuracion_invalida_se_informa(invalida):
    with pytest.raises(ConfiguracionFallasError, match="consultar|x"):
        InyectorFallas(invalida)


@pytest.mark.parametrize(
    "invalida",
    [
        f"op:{chr(0x0663)}",  # dígito arábigo-índico: isdigit() lo acepta, int() también
        "op:+1",
        "op:--1",
        "op:1,op:2",
        "Op Mal:1",
    ],
)
def test_configuracion_estricta_rechaza_lo_ambiguo(invalida):
    with pytest.raises(ConfiguracionFallasError, match=VARIABLE):
        InyectorFallas(invalida)


def test_operacion_repetida_se_nombra_en_el_error():
    with pytest.raises(ConfiguracionFallasError, match="repetida.*op"):
        InyectorFallas("op:1, op:2")


def test_desde_entorno_lee_la_variable(monkeypatch):
    monkeypatch.setenv(VARIABLE, "op:1")
    inyector = desde_entorno()
    assert inyector.debe_fallar("op")
    assert not inyector.debe_fallar("op")


def test_decorador_devuelve_error_transitorio_sin_ejecutar_y_luego_ejecuta():
    llamadas = []
    inyector = InyectorFallas("consultar:1")

    @con_fallas(inyector, "consultar")
    def consultar():
        llamadas.append(1)
        return {"ok": True, "datos": []}

    primera = consultar()
    assert primera["ok"] is False
    assert primera["error"]["tipo"] == "transitorio"
    assert primera["error"]["codigo"] == "FALLA_TRANSITORIA"
    assert primera["error"]["reintentable"] is True
    assert llamadas == []
    assert consultar() == {"ok": True, "datos": []}
    assert llamadas == [1]
