from datetime import date

import pytest

from core_bancario_mcp.contexto import (
    Contexto,
    DetalleTransaccion,
    IntentosVerificacion,
    RegistroBloqueos,
    RegistroDisputas,
    RegistroEscalamientos,
)
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


# --- bloqueos y escalamientos (issue #7) ---


def _tarjeta(tarjeta_id: str):
    return Repositorio(hoy=date(2026, 10, 23)).tarjetas[tarjeta_id]


def test_estado_inicial_de_la_tarjeta_se_respeta():
    bloqueos = RegistroBloqueos()
    assert bloqueos.estado_de(_tarjeta("TAR-004")) == "bloqueada"
    assert bloqueos.estado_de(_tarjeta("TAR-001")) == "activa"


def test_bloquear_informa_si_ya_estaba_bloqueada():
    bloqueos = RegistroBloqueos()
    assert bloqueos.bloquear(_tarjeta("TAR-001"), "Sospecha de fraude") is False
    assert bloqueos.estado_de(_tarjeta("TAR-001")) == "bloqueada"
    assert bloqueos.bloquear(_tarjeta("TAR-001"), "Otra vez") is True
    assert bloqueos.bloquear(_tarjeta("TAR-004"), "Ya venía bloqueada") is True


def _detalle(transaccion_id: str, monto: int) -> DetalleTransaccion:
    return DetalleTransaccion(
        transaccion_id=transaccion_id,
        fecha="2026-10-22",
        monto=monto,
        comercio="Comercio Ficticio",
        caso_disputa=None,
    )


def test_escalamientos_secuenciales_con_total_y_estado():
    escalamientos = RegistroEscalamientos()
    primero = escalamientos.registrar(
        "umbral",
        "CLI-001",
        "Nombre Ficticio",
        (_detalle("TRX-001", 180000), _detalle("TRX-002", 1250000)),
        "Consulté los cobros",
        "Revisar la disputa",
    )
    segundo = escalamientos.registrar(
        "persona_solicitada", None, None, (), "Ninguna", "Contactar al cliente"
    )
    assert (primero.id, segundo.id) == ("ESC-0001", "ESC-0002")
    assert primero.total == 1430000
    assert segundo.total == 0
    assert primero.estado == segundo.estado == "pendiente_analista"
    assert escalamientos.todos() == [primero, segundo]


def test_cada_contexto_tiene_sus_propios_bloqueos_y_escalamientos():
    repositorio = Repositorio(hoy=date(2026, 10, 23))
    uno = Contexto(repositorio, InyectorFallas(None))
    otro = Contexto(repositorio, InyectorFallas(None))
    uno.bloqueos.bloquear(repositorio.tarjetas["TAR-001"], "x")
    uno.escalamientos.registrar("otra", "CLI-001", "N", (), "a", "b")
    assert otro.bloqueos.estado_de(repositorio.tarjetas["TAR-001"]) == "activa"
    assert otro.escalamientos.todos() == []
