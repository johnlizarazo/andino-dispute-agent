from datetime import date

import pytest

from core_bancario_mcp.contexto import Contexto, IntentosVerificacion, RegistroDisputas
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


# --- registro de disputas (issue #6) ---


def _transaccion(transaccion_id: str):
    return Repositorio(hoy=date(2026, 10, 23)).obtener_transaccion(transaccion_id)


def test_casos_secuenciales_desde_caso_0001():
    disputas = RegistroDisputas()
    primero = disputas.abrir(_transaccion("TRX-001"), "No reconozco el cobro")
    segundo = disputas.abrir(_transaccion("TRX-003"), "No reconozco el cobro")
    assert (primero.id, segundo.id) == ("CASO-0001", "CASO-0002")


def test_caso_copia_monto_y_queda_abierto():
    caso = RegistroDisputas().abrir(_transaccion("TRX-001"), "No lo reconozco")
    assert (caso.transaccion_id, caso.monto, caso.motivo, caso.estado) == (
        "TRX-001",
        180000,
        "No lo reconozco",
        "abierta",
    )


def test_caso_de_antes_y_despues_de_abrir():
    disputas = RegistroDisputas()
    assert disputas.caso_de("TRX-001") is None
    caso = disputas.abrir(_transaccion("TRX-001"), "x")
    assert disputas.caso_de("TRX-001") == caso


def test_abrir_dos_veces_la_misma_transaccion_falla():
    disputas = RegistroDisputas()
    disputas.abrir(_transaccion("TRX-001"), "x")
    with pytest.raises(ValueError, match="TRX-001"):
        disputas.abrir(_transaccion("TRX-001"), "x")


def test_cada_contexto_tiene_su_propio_registro():
    repositorio = Repositorio(hoy=date(2026, 10, 23))
    uno = Contexto(repositorio, InyectorFallas(None))
    otro = Contexto(repositorio, InyectorFallas(None))
    uno.disputas.abrir(repositorio.obtener_transaccion("TRX-001"), "x")
    assert otro.disputas.caso_de("TRX-001") is None


def test_numero_de_caso_no_depende_de_cuantos_casos_quedan():
    disputas = RegistroDisputas()
    disputas.abrir(_transaccion("TRX-001"), "x")
    disputas.abrir(_transaccion("TRX-003"), "x")
    disputas._casos.clear()  # simula casos cerrados en el futuro
    assert disputas.abrir(_transaccion("TRX-004"), "x").id == "CASO-0003"
