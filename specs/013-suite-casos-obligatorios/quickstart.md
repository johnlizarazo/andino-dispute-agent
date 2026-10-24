# Quickstart: Suite de casos obligatorios y README

**Feature**: [spec.md](spec.md) · **Contrato**: [contracts/casos.md](contracts/casos.md)

## 1. Tests deterministas (sin credencial)

```bash
uv run pytest
```

Esperado: todo en verde, incluidos `tests/escenarios/test_registro.py` (armado del registro
con mensajes del SDK construidos a mano) y `tests/escenarios/test_mensajes.py` (ningún mensaje
de la suite está en el prompt). Los escenarios `e2e` se omiten.

## 2. Suite de casos obligatorios (con credencial)

```bash
uv run pytest -m e2e tests/escenarios/test_casos_obligatorios.py
```

Esperado: 6 passed, en menos de 10 minutos (SC-005).

## 3. Todos los escenarios

```bash
uv run pytest -m e2e
```

Esperado: la suite más los escenarios que se mantienen (delegación, eventos y regla 1 sin
prompt), todos en verde; ya no hay tests de falla transitoria fuera de la suite.

## 4. README en 5 minutos

En una máquina con Python 3.14 y `uv` instalados (Windows y, si es posible, Linux/macOS), una
persona que no conoce el proyecto sigue solo el README: instala, define la credencial para la
sesión, corre `uv run pytest`, abre `uv run andino-chat` y reproduce un caso de la tabla.
Anotar el tiempo (SC-004).
