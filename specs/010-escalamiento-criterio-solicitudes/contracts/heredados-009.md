# Contrato: ajustes heredados del #9

Fundamento en [research.md R7](../research.md). Son los no bloqueantes de las revisiones del
PR #23.

| Ajuste | Archivo | Comportamiento esperado | Test |
|---|---|---|---|
| (a) Herramienta explícita | `src/agente_disputas/controles.py` | entrada sin `tool_name` legible → `Negacion("desconocida", "FALLA_CONTROL")` | `test_entrada_mal_formada_niega` comprueba la herramienta |
| (b) Razón del umbral | `src/agente_disputas/controles.py` | la razón de `REQUIERE_ANALISTA` muestra el umbral de la política con formato `$500.000` | con una `Politica` de umbral 300000, la razón dice `$300.000` |
| (c) Código redundante | `src/agente_disputas/controles.py` | un solo `return {}` en `despues_de_verificar` | — |
| (d) Intención explícita | `src/agente_disputas/configuracion.py` | `if controles is None:` | — |
| (e) Línea larga | `src/agente_disputas/__init__.py` | docstring ≤ 95 caracteres por línea | — |
| Tareas del #9 | `specs/009-hooks-sdk-r1-r2/tasks.md` | T024 y T025 marcadas | hecho en el commit de la spec |
