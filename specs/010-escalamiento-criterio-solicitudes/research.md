# Research: Escalamiento con criterio y solicitudes múltiples (issue #10)

API verificada por introspección de `claude-agent-sdk` 0.2.168 (`types.py`: `HookEvent`,
`StopHookInput`, `UserPromptSubmitHookInput`, `SyncHookJSONOutput`).

## R1. Hook `Stop` del SDK

- **Hallazgo**:
  - `HookEvent` incluye `"Stop"` y `"UserPromptSubmit"`.
  - `StopHookInput`: `stop_hook_active: bool` (verdadero si el modelo ya sigue por un bloqueo
    anterior de un hook `Stop`) y `last_assistant_message`.
  - Para impedir el cierre, el callback devuelve `{"decision": "block", "reason": "<razón>"}`
    (`SyncHookJSONOutput.decision: Literal["block"]`); el modelo recibe la razón y continúa en
    el mismo turno. `{}` deja terminar.
- **Decision**: un `HookMatcher(matcher=None, hooks=[controles.antes_de_terminar])` en
  `"Stop"`. El tope lo cuenta nuestro estado (`cierres_impedidos`), no `stop_hook_active`: así
  el tope es exacto (2) y se prueba sin el CLI.
- **Alternatives considered**: usar solo `stop_hook_active` (permitiría un único bloqueo, sin
  control del número); obligar desde el prompt (la constitución exige un hook).

## R2. Qué crea un pendiente (FR-001)

- **Decision**:
  - **Negación por umbral del control** (`PreToolUse`, código `REQUIERE_ANALISTA`): la
    `Decision` lleva la transacción; `antes_de_herramienta` registra el pendiente con causa
    `umbral` al negar.
  - **Rechazo del core**: nuevo `PostToolUse` sobre `mcp__core-bancario__iniciar_disputa`. Si
    `leer_respuesta` da `ok: false` con `codigo` `FUERA_DE_POLITICA` → causa
    `fuera_de_politica`; con `REQUIERE_ANALISTA` (segunda defensa del core) → causa `umbral`.
    La transacción sale del `transaccion_id` de `tool_input` (sin espacios).
  - Otras negaciones (`SIN_IDENTIDAD`, `CLIENTE_DISTINTO`, `TRANSACCION_NO_CONFIRMADA`,
    `FALLA_CONTROL`) y otros errores del core no crean pendiente.
- **Rationale**: las dos vías por las que una disputa termina en "requiere analista" o "fuera
  de política" quedan cubiertas; los códigos vienen del contrato del core (principio V), no de
  interpretar texto.

## R3. Qué limpia un pendiente (FR-003, FR-005)

- **Decision**:
  - Nuevo `PostToolUse` sobre `mcp__core-bancario__escalar_a_analista`: si la respuesta es
    `ok: true`, quita los pendientes cuya transacción está en `tool_input["transacciones"]`
    **y** cuya causa coincide con `tool_input["causa"]`. Los ids se leen con la misma función
    que usa el core (`lista_de_ids`: lista o texto con lista JSON, sin espacios), que pasa a ser
    pública en `core_bancario_mcp.bloqueo_escalamiento`.
  - Hook `UserPromptSubmit` (`controles.al_recibir_mensaje`): al llegar un nuevo mensaje del
    cliente vacía los pendientes y pone `cierres_impedidos` en 0.
- **Rationale**:
  - Exigir la causa y la transacción hace que el handoff sea completo para ese caso (el core
    ya exige cliente, transacciones, acciones y recomendación para `umbral` y
    `fuera_de_politica`).
  - "El cliente reconoce el cobro" es interpretar al cliente; no se detecta. Como el `Stop`
    obliga a escalar antes de terminar el turno, el pendiente solo sobrevive al turno si se
    alcanzó el tope, y con el nuevo mensaje decide el agente. Si el cliente insiste, la nueva
    negación crea otro pendiente.
  - `UserPromptSubmit` funciona igual para la línea de comandos y para la interfaz del #12, sin
    que cada interfaz tenga que avisar a los controles.
- **Alternatives considered**: limpiar con cualquier escalamiento exitoso (no garantiza que el
  analista reciba la transacción); detectar "lo reconozco" con palabras (prohibido por la
  constitución); un parámetro extra en una herramienta del core para "descartar" (otra
  superficie para que el modelo evite escalar).

## R4. Tope y falla visible (FR-004)

- **Decision**:
  - `antes_de_terminar`: si hay pendientes y `cierres_impedidos < MAXIMO_CIERRES_IMPEDIDOS`
    (2), suma uno y bloquea con la razón; si no hay pendientes o se alcanzó el tope, devuelve
    `{}`.
  - La razón lista cada transacción con su causa: "Antes de terminar, escala con
    escalar_a_analista: TRX-… (causa umbral). Incluye cliente, transacciones, acciones
    realizadas y acción recomendada."
  - **Falla visible**: `conversar` recibe los `controles`; tras cada turno, si quedan
    pendientes, escribe `AVISO_ESCALAMIENTO_PENDIENTE` ("No pude pasar tu caso a un analista en
    este momento. Por favor, inténtalo de nuevo más tarde.") después de la respuesta. No
    depende de lo que diga el modelo.
  - Una excepción dentro de `antes_de_terminar` deja terminar (no bloquea): forzar un ciclo por
    un error del control sería peor; el pendiente queda y el aviso lo hace visible. Es la única
    falla abierta y se justifica porque no autoriza ninguna operación.
- **Alternatives considered**: tope por pendiente (más estado sin beneficio); error del turno
  en lugar de aviso (perdería la respuesta del resto de asuntos).

## R5. El pendiente no bloquea lo resoluble (FR-006)

- **Decision**: los pendientes solo los lee `antes_de_terminar`; `antes_de_herramienta` no los
  consulta. Test determinista con el mensaje de ejemplo: tras negar `TRX-002` por umbral,
  `TRX-001` y el bloqueo de la 4821 se autorizan, y `antes_de_terminar` bloquea hasta escalar
  `TRX-002`.

## R6. Regla 4 y criterio: prompt v4 y descripción (FR-007 a FR-011)

- **Decision**:
  - Sección "Cuándo escalar y cuándo no" en el prompt: persona a pedido → escalar de inmediato
    con causa `persona_solicitada`, sin buscar ni verificar (sin `cliente_id` si no se conoce);
    no escalar disputas bajo el umbral, bloqueos ni por molestia.
  - Sección "Varios asuntos": listar los asuntos, resolver cada uno (lo resoluble primero no es
    obligatorio, pero ninguno queda sin respuesta) y responder una sola vez con el resultado de
    cada uno.
  - `<ejemplos>` con 4 ejemplos, cada uno con mensaje del cliente y acción esperada
    (herramientas en orden y qué se responde):
    1. Pide una persona en el primer mensaje → `escalar_a_analista` con `persona_solicitada`
       de inmediato.
    2. "Una persona me clonó la tarjeta" → no es un pedido de persona: identificar, verificar,
       bloquear y ofrecer revisar cobros.
    3. Varios asuntos (un cobro bajo el umbral, uno sobre el umbral y un bloqueo) → disputar el
       menor, bloquear, la disputa del mayor se niega y se escala con causa `umbral`; una sola
       respuesta.
    4. Cobro del exterior antiguo → la disputa responde fuera de política → escalar con causa
       `fuera_de_politica`.
  - Datos de los ejemplos: tarjetas, montos y comercios que **no** existen en
    `core_bancario_mcp/datos` ni en `tests/escenarios` (p. ej. tarjeta 7730, $95.000 y
    $2.300.000). Un test determinista lo comprueba (ningún `ultimos4` de los datos, ningún
    monto de las transacciones ni mensaje de `tests/escenarios` aparece dentro de
    `<ejemplos>`).
  - `VERSION_PROMPT = "4"`.
  - `DESCRIPCION_ESCALAR` (core): agrega "No la uses solo porque el cliente esté molesto o
    insatisfecho; si el caso se puede resolver (disputa bajo el umbral, bloqueo), resuélvelo".
- **Rationale**: la regla 4 se orienta con ejemplos positivos y negativos que muestran la
  acción (principio II); el test de separación evita que un escenario pase por memoria
  (principio VI).
- **Alternatives considered**: hook que busca "persona"/"asesor" (prohibido); más de 5
  ejemplos (el issue fija 3 a 5).

## R7. Ajustes heredados del #9 (FR-012)

- (a) `antes_de_herramienta`: si `tool_name` no es texto, la negación se registra con
  herramienta `"desconocida"`.
- (b) La razón de `REQUIERE_ANALISTA` se arma con el umbral de la política
  (`f"... supera ${umbral:,} ..."` con separador de miles en punto, p. ej. "$500.000").
- (c) Un solo `return {}` en `despues_de_verificar`.
- (d) `if controles is None:` en `crear_opciones`.
- (e) Docstring de `src/agente_disputas/__init__.py` en dos líneas (≤ 95 caracteres).
