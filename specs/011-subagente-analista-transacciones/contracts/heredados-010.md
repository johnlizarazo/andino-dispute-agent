# Contrato: ajustes heredados del #10

Fundamento en [research.md R6](../research.md). Son los no bloqueantes de las revisiones del
PR #24.

| Ajuste | Archivo | Comportamiento esperado | Test |
|---|---|---|---|
| (a) Texto de T006 | `specs/010-escalamiento-criterio-solicitudes/tasks.md` | nombra `DISPUTA_EXISTENTE` | — |
| (b) Entradas mal formadas | `src/agente_disputas/test_controles.py` | `antes_de_terminar` y `al_recibir_mensaje` con `None` y `{}` devuelven `{}` sin lanzar | nuevo |
| (c) Forma del callback | `src/agente_disputas/controles.py` | `al_recibir_mensaje` con `suppress(Exception)` como los demás | (b) |
| Tareas del #10 | `specs/010-escalamiento-criterio-solicitudes/tasks.md` | T022 y T023 marcadas | hecho en el commit de la spec |
