import json
import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest

from core_bancario_mcp.repositorio import DatosInvalidosError, Repositorio, Transaccion

DATOS = Path(__file__).with_name("datos")


def _cobros_tarjeta(repo: Repositorio, ultimos4: str):
    (tarjeta,) = [t for t in repo.tarjetas.values() if t.ultimos4 == ultimos4]
    return [t for t in repo.transacciones.values() if t.tarjeta_id == tarjeta.id]


@pytest.mark.parametrize(
    ("hoy", "ayer"),
    [
        (date(2027, 1, 1), date(2026, 12, 31)),  # fin de año
        (date(2026, 3, 1), date(2026, 2, 28)),  # fin de febrero
        (date(2026, 11, 1), date(2026, 10, 31)),  # fin de mes
    ],
)
def test_tarjeta_4821_tiene_los_dos_cobros_de_ayer(hoy, ayer):
    repo = Repositorio(hoy=hoy)
    de_ayer = [t for t in _cobros_tarjeta(repo, "4821") if t.fecha == ayer]
    assert sorted(t.monto for t in de_ayer) == [180000, 1250000]


def test_dos_clientes_con_el_mismo_nombre_y_documentos_distintos():
    repo = Repositorio(hoy=date(2026, 10, 23))
    por_nombre = {}
    for cliente in repo.clientes.values():
        por_nombre.setdefault(cliente.nombre, []).append(cliente)
    homonimos = [grupo for grupo in por_nombre.values() if len(grupo) == 2]
    assert len(homonimos) == 1
    assert homonimos[0][0].documento != homonimos[0][1].documento


def test_existe_un_cobro_en_el_exterior_con_mas_de_90_dias():
    hoy = date(2026, 10, 23)
    repo = Repositorio(hoy=hoy)
    limite = repo.politica.dias_maximos_disputa_exterior
    assert limite == 90
    assert any(
        t.pais != "CO" and (hoy - t.fecha).days > limite
        for t in repo.transacciones.values()
    )


def test_datos_de_borde_para_otros_tickets():
    repo = Repositorio(hoy=date(2026, 10, 23))
    assert any(t.monto == 500000 for t in repo.transacciones.values())
    assert any(t.estado == "bloqueada" for t in repo.tarjetas.values())


def test_cliente_de_la_transaccion_se_deriva_de_la_tarjeta():
    repo = Repositorio(hoy=date(2026, 10, 23))
    for transaccion in repo.transacciones.values():
        tarjeta = repo.tarjetas[transaccion.tarjeta_id]
        assert transaccion.cliente_id == tarjeta.cliente_id


def test_datos_solo_con_forma_ficticia():
    repo = Repositorio(hoy=date(2026, 10, 23))
    assert all(len(t.ultimos4) == 4 for t in repo.tarjetas.values())
    assert all(c.documento.startswith("CC-FIC-") for c in repo.clientes.values())


# --- consulta por id (la reutiliza el hook del umbral, issue #9) ---


def test_obtener_transaccion_devuelve_monto_titular_y_fecha():
    repo = Repositorio(hoy=date(2026, 10, 23))
    transaccion = repo.obtener_transaccion("TRX-002")
    assert transaccion.monto == 1250000
    assert transaccion.cliente_id == "CLI-001"
    assert transaccion.fecha == date(2026, 10, 22)


def test_obtener_transaccion_inexistente_devuelve_none():
    repo = Repositorio(hoy=date(2026, 10, 23))
    assert repo.obtener_transaccion("TRX-999") is None


def test_obtener_transaccion_coincide_con_los_datos_para_todas():
    repo = Repositorio(hoy=date(2026, 10, 23))
    crudas = json.loads((DATOS / "transacciones.json").read_text(encoding="utf-8"))
    for cruda in crudas:
        assert repo.obtener_transaccion(cruda["id"]).monto == cruda["monto"]


# --- validación de datos mal formados ---


def _copia(tmp_path: Path) -> Path:
    destino = tmp_path / "datos"
    shutil.copytree(DATOS, destino)
    return destino


def _editar(carpeta: Path, archivo: str, cambio) -> None:
    ruta = carpeta / archivo
    contenido = json.loads(ruta.read_text(encoding="utf-8"))
    cambio(contenido)
    ruta.write_text(json.dumps(contenido, ensure_ascii=False), encoding="utf-8")


@pytest.mark.parametrize(
    ("archivo", "cambio", "pista"),
    [
        ("tarjetas.json", lambda d: d[0].update(ultimos4="48210"), "ultimos4"),
        ("clientes.json", lambda d: d[0].update(documento="CC-0001"), "documento"),
        ("clientes.json", lambda d: d.append(dict(d[0])), "duplicado"),
        ("tarjetas.json", lambda d: d[0].update(cliente_id="CLI-999"), "CLI-999"),
        ("transacciones.json", lambda d: d[0].update(tarjeta_id="TAR-999"), "TAR-999"),
        ("transacciones.json", lambda d: d[0].update(monto=0), "monto"),
        ("transacciones.json", lambda d: d[0].update(dias_atras=-1), "dias_atras"),
        ("transacciones.json", lambda d: d[0].pop("comercio"), "comercio"),
        ("clientes.json", lambda d: d[0].update(extra="x"), "extra"),
    ],
)
def test_datos_invalidos_impiden_cargar(tmp_path, archivo, cambio, pista):
    carpeta = _copia(tmp_path)
    _editar(carpeta, archivo, cambio)
    with pytest.raises(DatosInvalidosError, match=pista):
        Repositorio(hoy=date(2026, 10, 23), carpeta=carpeta)


def _digitos_arabigo_indicos(texto: str) -> str:
    return "".join(chr(0x0660 + int(c)) for c in texto)


@pytest.mark.parametrize(
    ("archivo", "cambio", "pista"),
    [
        ("clientes.json", lambda d: d[0].update(id=1), "id"),
        ("clientes.json", lambda d: d[0].update(nombre=""), "nombre"),
        ("clientes.json", lambda d: d[0].update(documento=1), "documento"),
        ("tarjetas.json", lambda d: d[0].update(ultimos4=4821), "ultimos4"),
        ("tarjetas.json", lambda d: d[0].update(cliente_id=None), "cliente_id"),
        ("transacciones.json", lambda d: d[0].update(monto=1.5), "monto"),
        ("transacciones.json", lambda d: d[0].update(monto=True), "monto"),
        ("transacciones.json", lambda d: d[0].update(dias_atras="1"), "dias_atras"),
        (
            "politicas.json",
            lambda d: d.update(umbral_disputa_automatica="500000"),
            "umbral_disputa_automatica",
        ),
        ("tarjetas.json", lambda d: d[0].update(estado="perdida"), "estado"),
        ("transacciones.json", lambda d: d[0].update(pais="COL"), "pais"),
        (
            "clientes.json",
            lambda d: d[0].update(dato_verificacion="19x7"),
            "dato_verificacion",
        ),
        (
            "tarjetas.json",
            lambda d: d[0].update(ultimos4=_digitos_arabigo_indicos("4821")),
            "ultimos4",
        ),
    ],
)
def test_tipos_y_valores_incorrectos_impiden_cargar(tmp_path, archivo, cambio, pista):
    carpeta = _copia(tmp_path)
    _editar(carpeta, archivo, cambio)
    with pytest.raises(DatosInvalidosError) as excinfo:
        Repositorio(hoy=date(2026, 10, 23), carpeta=carpeta)
    assert archivo in str(excinfo.value)
    assert pista in str(excinfo.value)


def test_registro_que_no_es_objeto_nombra_su_posicion(tmp_path):
    carpeta = _copia(tmp_path)
    ruta = carpeta / "tarjetas.json"
    tarjetas = json.loads(ruta.read_text(encoding="utf-8"))
    posicion = len(tarjetas)
    ruta.write_text(json.dumps([*tarjetas, 5]), encoding="utf-8")
    with pytest.raises(DatosInvalidosError, match=f"tarjetas.json posición {posicion}"):
        Repositorio(hoy=date(2026, 10, 23), carpeta=carpeta)


@pytest.mark.parametrize(
    ("archivo", "contenido"),
    [("clientes.json", {"id": "CLI-001"}), ("politicas.json", [])],
)
def test_archivo_con_estructura_incorrecta_impide_cargar(tmp_path, archivo, contenido):
    carpeta = _copia(tmp_path)
    (carpeta / archivo).write_text(json.dumps(contenido), encoding="utf-8")
    with pytest.raises(DatosInvalidosError, match=archivo):
        Repositorio(hoy=date(2026, 10, 23), carpeta=carpeta)


def test_archivo_ausente_impide_cargar(tmp_path):
    carpeta = _copia(tmp_path)
    (carpeta / "politicas.json").unlink()
    with pytest.raises(DatosInvalidosError, match="politicas.json"):
        Repositorio(hoy=date(2026, 10, 23), carpeta=carpeta)


def test_json_invalido_impide_cargar(tmp_path):
    carpeta = _copia(tmp_path)
    (carpeta / "clientes.json").write_text("{no es json", encoding="utf-8")
    with pytest.raises(DatosInvalidosError, match="clientes.json"):
        Repositorio(hoy=date(2026, 10, 23), carpeta=carpeta)


# --- política y tarjetas del cliente (issue #6; el hook del umbral del #9 reutiliza Politica) ---

HOY = date(2026, 10, 23)


def _transaccion(dias: int, pais: str, monto: int = 1000) -> Transaccion:
    return Transaccion(
        id="TRX-X",
        tarjeta_id="TAR-001",
        cliente_id="CLI-001",
        fecha=HOY - timedelta(days=dias),
        monto=monto,
        comercio="Comercio Ficticio",
        pais=pais,
        estado="aplicada",
    )


def test_repositorio_guarda_su_hoy():
    assert Repositorio(hoy=HOY).hoy == HOY


def test_umbral_es_inclusivo():
    politica = Repositorio(hoy=HOY).politica
    assert politica.requiere_analista(500000) is False
    assert politica.requiere_analista(500001) is True


@pytest.mark.parametrize(
    ("dias", "pais", "cubre"),
    [(90, "US", True), (91, "US", False), (120, "CO", True), (121, "CO", False)],
)
def test_politica_cubre_hasta_el_limite_inclusive(dias, pais, cubre):
    politica = Repositorio(hoy=HOY).politica
    assert politica.cubre(_transaccion(dias, pais), HOY) is cubre


def test_tarjetas_de_solo_devuelve_las_del_cliente():
    repo = Repositorio(hoy=HOY)
    assert [t.id for t in repo.tarjetas_de("CLI-001", "4821")] == ["TAR-001"]
    assert repo.tarjetas_de("CLI-002", "4821") == []
    assert repo.tarjetas_de("CLI-999", "4821") == []


@pytest.mark.parametrize(("pais", "limite"), [("CO", 120), ("US", 90)])
def test_limite_de_dias_segun_el_pais(pais, limite):
    politica = Repositorio(hoy=HOY).politica
    assert politica.limite_dias(_transaccion(1, pais)) == limite
