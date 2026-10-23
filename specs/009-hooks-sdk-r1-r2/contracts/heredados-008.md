# Contrato: ajustes heredados del #8

Fundamento en [research.md R8](../research.md). Son los no bloqueantes de las revisiones del
PR #22.

| Ajuste | Archivo | Comportamiento esperado | Test |
|---|---|---|---|
| (a) Sin cliente, sin transacciones | `src/core_bancario_mcp/bloqueo_escalamiento.py` | `persona_solicitada` sin `cliente_id` y con `transacciones` no vacía → `validacion` / `PARAMETRO_INVALIDO`, igual exista o no la transacción | reemplaza `test_persona_solicitada_sin_cliente_acepta_transacciones`: `["TRX-001"]` y `["TRX-999"]` dan respuestas idénticas |
| (b) Arranque sin traza | `src/agente_disputas/test_cli.py` | `main()` con `KeyboardInterrupt` → despedida, código 0; con `CLINotFoundError` → mensaje en stderr, código 1 | nuevos, simulando `_ejecutar` |
| (c) T007 del #8 | `specs/008-ciclo-agentico-mcp/tasks.md` | el texto describe las 3 habilitadas y las 3 deshabilitadas, como quedó en el #8 | — |
| (d) Tipo completo | `src/agente_disputas/ciclo.py` | `procesar_turno(mensajes: AsyncIterable[Message])` | — |
| (e) Líneas largas | `src/agente_disputas/prompts.py`, `cli.py` | ninguna línea de más de 95 caracteres | — |
