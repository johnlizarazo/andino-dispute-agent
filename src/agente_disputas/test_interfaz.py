import sys
import types
from pathlib import Path

import nest_asyncio

from agente_disputas import interfaz


def test_main_arranca_esta_interfaz_sin_nest_asyncio(monkeypatch):
    llamadas = []
    falso = types.ModuleType("chainlit.cli")
    # Importar el CLI real aplicaría nest_asyncio en este proceso: se usa uno falso.
    falso.cli = lambda argumentos: llamadas.append((argumentos, nest_asyncio.apply()))
    monkeypatch.setitem(sys.modules, "chainlit.cli", falso)
    monkeypatch.setattr(nest_asyncio, "apply", nest_asyncio.apply)
    monkeypatch.setattr(sys, "argv", ["andino-chat", "--headless"])

    interfaz.main()

    [(argumentos, aplicado)] = llamadas
    assert argumentos == ["run", str(Path(interfaz.__file__).resolve()), "--headless"]
    assert aplicado is None  # apply quedó neutralizado antes de importar el CLI


def test_la_bienvenida_no_menciona_ordenes_de_la_terminal():
    assert "/salir" not in interfaz.BIENVENIDA_WEB
    assert "Evento" in interfaz.BIENVENIDA_WEB
