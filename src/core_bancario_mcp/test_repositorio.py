import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from core_bancario_mcp.repositorio import DatosInvalidosError, Repositorio

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
