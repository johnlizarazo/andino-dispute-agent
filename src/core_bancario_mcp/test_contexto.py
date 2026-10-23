from datetime import date

from core_bancario_mcp.contexto import Contexto, IntentosVerificacion
from core_bancario_mcp.fallas import InyectorFallas
from core_bancario_mcp.repositorio import Repositorio


def _fallar(intentos: IntentosVerificacion, cliente_id: str, veces: int) -> None:
    for _ in range(veces):
        intentos.registrar_fallo(cliente_id)


def test_cliente_nuevo_no_esta_agotado():
    assert not IntentosVerificacion().agotados("CLI-001")


def test_tres_fallos_agotan_y_dos_no():
    intentos = IntentosVerificacion()
    assert IntentosVerificacion.MAXIMO == 3
    _fallar(intentos, "CLI-001", 2)
    assert not intentos.agotados("CLI-001")
    intentos.registrar_fallo("CLI-001")
    assert intentos.agotados("CLI-001")


def test_reiniciar_tras_dos_fallos_vuelve_a_cero():
    intentos = IntentosVerificacion()
    _fallar(intentos, "CLI-001", 2)
    intentos.reiniciar("CLI-001")
    _fallar(intentos, "CLI-001", 2)
    assert not intentos.agotados("CLI-001")


def test_cliente_agotado_sigue_agotado():
    intentos = IntentosVerificacion()
    _fallar(intentos, "CLI-001", 5)
    assert intentos.agotados("CLI-001")


def test_fallos_de_un_cliente_no_afectan_a_otro():
    intentos = IntentosVerificacion()
    _fallar(intentos, "CLI-001", 3)
    assert not intentos.agotados("CLI-002")


def test_cada_contexto_tiene_sus_propios_intentos():
    repositorio = Repositorio(hoy=date(2026, 10, 23))
    uno = Contexto(repositorio, InyectorFallas(None))
    otro = Contexto(repositorio, InyectorFallas(None))
    _fallar(uno.intentos, "CLI-001", 3)
    assert uno.intentos.agotados("CLI-001")
    assert not otro.intentos.agotados("CLI-001")
