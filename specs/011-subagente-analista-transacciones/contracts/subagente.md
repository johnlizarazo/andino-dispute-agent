# Contrato: subagente y delegación

Fundamento en [research.md](../research.md) R1 a R5; entidades en
[data-model.md](../data-model.md).

## `src/agente_disputas/analista.py` (nuevo)

- `NOMBRE = "analista-transacciones"`.
- `HERRAMIENTA_DELEGAR = "Agent"` (o `"Task"` según la sonda; research R1).
- `prompt_analista(politica: Politica) -> str`: instrucciones del subagente con
  `politica.umbral_disputa_automatica`, `dias_maximos_disputa_exterior` y
  `dias_maximos_disputa_nacional` formateados (`$500.000`, `90`, `120`), el formato del bloque
  `<contexto>`, el orden de clasificación y el formato de `<analisis>`; prohíbe inventar
  transacciones y hablar con el cliente.
- `definir_analista(politica: Politica) -> AgentDefinition`: `description` (cuándo usarlo),
  `prompt=prompt_analista(politica)`, `tools=["mcp__core-bancario__consultar_transacciones"]`,
  `model="inherit"`, `maxTurns=8`.
- `leer_contexto(prompt: str) -> tuple[dict | None, list[str]]`: extrae y valida el bloque
  `<contexto>`; devuelve el contexto normalizado (sin espacios) y la lista de campos inválidos
  o faltantes (vacía si es válido).

## `src/agente_disputas/controles.py`

- Constantes `SUBAGENTE_NO_PERMITIDO`, `CONTEXTO_INCOMPLETO` con razones en `RAZONES`
  (la de `CONTEXTO_INCOMPLETO` se arma con los nombres de campo: "Falta o es inválido en el
  bloque <contexto>: ultimos4, fecha_hasta.").
- `antes_de_delegar(entrada, tool_use_id, contexto) -> dict` (`PreToolUse`): orden de
  research R2; niega con la misma salida `deny` del #9 y registra la `Negacion`; autoriza con
  `{}`. Nunca lanza.
- `hooks()` agrega `HookMatcher(matcher="Agent|Task", hooks=[antes_de_delegar])` en
  `PreToolUse`.
- (c) heredado: `al_recibir_mensaje` con `suppress(Exception)`; si la entrada trae `agent_id`
  (research R3), no vacía nada.

## `src/agente_disputas/configuracion.py`

- Con `controles.politica` disponible: `agents={NOMBRE: definir_analista(politica)}`,
  `tools=[HERRAMIENTA_DELEGAR]`, `allowed_tools` = las 6 del core + `HERRAMIENTA_DELEGAR`.
- Sin política (datos no cargados): `agents=None`, `tools=[]` y `allowed_tools` sin la
  delegación (falla cerrada).

## Tests deterministas (sin API)

`src/agente_disputas/test_analista.py`:

1. `definir_analista`: `tools` es exactamente `["mcp__core-bancario__consultar_transacciones"]`,
   `model == "inherit"`, `maxTurns == 8`.
2. `prompt_analista` con la política real contiene `$500.000`, `90` y `120`; con una política de
   umbral 300000 contiene `$300.000` y no `$500.000`.
3. `leer_contexto`: bloque válido → contexto normalizado y `[]`; sin bloque, JSON inválido,
   cada campo faltante, `ultimos4` "48A1", fecha "2026-13-01", `fecha_desde > fecha_hasta`,
   `montos_reportados` con 0, negativo, texto o no lista → la lista nombra el campo; lista de
   montos vacía es válida.

`src/agente_disputas/test_controles.py`:

4. Delegación sin verificar → `SIN_IDENTIDAD`; con otro `subagent_type` → `SUBAGENTE_NO_
   PERMITIDO`; sin bloque o con campos inválidos → `CONTEXTO_INCOMPLETO` con los nombres de
   campo en la razón; con `cliente_id` CLI-002 y CLI-001 verificado → `CLIENTE_DISTINTO` sin
   "CLI-002" en la razón; válida → `{}`; entrada mal formada → `FALLA_CONTROL`.
5. Una consulta con `agent_id` (simulando el subagente) sobre otro cliente se niega igual
   (`CLIENTE_DISTINTO`), y sobre el verificado se autoriza.
6. (b) heredado: `antes_de_terminar` y `al_recibir_mensaje` con `None` y `{}` → `{}` sin lanzar;
   `al_recibir_mensaje` con `agent_id` no vacía pendientes.

`src/agente_disputas/test_configuracion.py`:

7. `agents` tiene solo `analista-transacciones`; `tools == ["Agent"]`; `allowed_tools` = 6 del
   core + `"Agent"`; `PreToolUse` incluye el matcher de delegación.
8. Con controles sin política: sin `agents`, `tools == []` y sin la delegación.

## Escenario `e2e` (`tests/escenarios/test_delegacion_e2e.py`)

- Mensaje (distinto de los ejemplos del prompt): una clienta ficticia CC-FIC-0001 se verifica
  y pide revisar los cobros de ayer de su tarjeta 4821 antes de reclamar.
- Espía en `antes_de_herramienta` y `antes_de_delegar` que registra `tool_name` y `agent_id`.
- Aserciones: hubo una delegación autorizada a `analista-transacciones`; al menos una consulta
  `consultar_transacciones` llegó a los controles con `agent_id` (FR-005); ninguna disputa sobre
  el umbral llegó al core.
