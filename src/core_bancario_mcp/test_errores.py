import pytest

from core_bancario_mcp.errores import Codigo, TipoError, error, exito


@pytest.mark.parametrize("datos", [{"id": "CLI-001"}, [1, 2], []])
def test_exito_envuelve_los_datos(datos):
    assert exito(datos) == {"ok": True, "datos": datos}


def test_busqueda_sin_resultados_es_exito_con_lista_vacia():
    assert exito([]) == {"ok": True, "datos": []}


@pytest.mark.parametrize(
    ("tipo", "reintentable"),
    [
        (TipoError.TRANSITORIO, True),
        (TipoError.VALIDACION, False),
        (TipoError.NEGOCIO, False),
        (TipoError.PERMISO, False),
    ],
)
def test_error_tiene_forma_completa_y_reintento_derivado_del_tipo(tipo, reintentable):
    respuesta = error(tipo, Codigo.NO_ENCONTRADO, "No existe.")
    assert respuesta == {
        "ok": False,
        "error": {
            "tipo": tipo.value,
            "codigo": "NO_ENCONTRADO",
            "mensaje": "No existe.",
            "reintentable": reintentable,
        },
    }


def test_solo_existen_los_cuatro_tipos_del_contrato():
    assert {t.value for t in TipoError} == {
        "transitorio",
        "validacion",
        "negocio",
        "permiso",
    }


def test_tipo_fuera_del_contrato_se_rechaza():
    with pytest.raises((TypeError, ValueError)):
        error("desconocido", Codigo.NO_ENCONTRADO, "x")
