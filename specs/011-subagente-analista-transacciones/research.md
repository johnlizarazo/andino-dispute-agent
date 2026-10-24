# Research: Subagente `analista-transacciones` (issue #11)

API verificada por introspección de `claude-agent-sdk` 0.2.168 (`types.py`: `AgentDefinition`,
`ClaudeAgentOptions.agents`, `_SubagentContextMixin`, `SubagentStartHookInput`).

## R1. Subagentes en el SDK

- **Hallazgo**:
  - `ClaudeAgentOptions.agents: dict[str, AgentDefinition]`; `AgentDefinition(description,
    prompt, tools, disallowedTools, model, mcpServers, maxTurns, permissionMode, ...)`.
  - El principal invoca un subagente con la herramienta de delegación del motor (`Agent`,
    antes llamada `Task`), cuyo argumento lleva el tipo de subagente y un texto de prompt. El
    subagente arranca con su propio prompt de sistema y **solo** ese texto: no recibe la
    conversación.
  - Los hooks de ciclo de herramientas (`PreToolUse`, `PostToolUse`) se disparan también para
    las herramientas que usa un subagente, por el mismo canal, con `agent_id` y `agent_type`
    en la entrada (`_SubagentContextMixin`: "Present only when the hook fires from inside a
    Task-spawned sub-agent").
  - El fin de un subagente dispara `SubagentStop`, no `Stop`.
- **Decision**:
  - `AgentDefinition` para `analista-transacciones` con `tools=["mcp__core-bancario__
    consultar_transacciones"]`, `model="inherit"`, `maxTurns` como salvaguarda (8) y sin
    `mcpServers` propio (hereda el `core-bancario` del principal).
  - El principal recibe la herramienta de delegación: `tools=["Agent"]` y `"Agent"` en
    `allowed_tools`; ninguna otra herramienta del motor.
  - Una **sonda con la API** (primera tarea de implementación) confirma el nombre de la
    herramienta (`Agent` o `Task`), los campos de su entrada (`subagent_type`, `prompt`,
    `description`) y que el `PreToolUse` de `consultar_transacciones` recibe `agent_id` cuando
    consulta el subagente. Si el nombre fuera `Task`, se usa ese; el matcher del control acepta
    ambos (`Agent|Task`).
- **Resultado de la sonda (T001)**: herramienta `Agent` con `description`, `prompt`,
  `subagent_type` y `run_in_background`; la consulta del subagente llega al `PreToolUse` con
  `agent_id` y `agent_type`; `UserPromptSubmit` no se dispara con la delegación. Sin
  `background=False` el subagente corre en segundo plano y el principal termina el turno sin su
  resultado: la definición fija `background=False` y el control de delegación niega
  `run_in_background` verdadero (`SEGUNDO_PLANO_NO_PERMITIDO`), así la clasificación siempre
  vuelve dentro del mismo turno y los controles del #10 siguen viendo el turno completo.
- **Alternatives considered**: un segundo `ClaudeSDKClient` llamado desde una herramienta MCP
  propia (más piezas, y perdería los hooks del principal sobre las consultas).

## R2. Contexto explícito verificable (FR-003, FR-004)

- **Decision**: la delegación lleva, dentro del prompt, un bloque
  `<contexto>{json}</contexto>` con:

  | Campo | Regla |
  |---|---|
  | `cliente_id` | texto; igual al cliente verificado (sin espacios) |
  | `ultimos4` | exactamente 4 dígitos |
  | `fecha_desde`, `fecha_hasta` | `AAAA-MM-DD` válidas, `fecha_desde <= fecha_hasta` |
  | `montos_reportados` | lista de enteros positivos (puede ir vacía) |

  Un `PreToolUse` sobre la herramienta de delegación (`Controles.antes_de_delegar`):
  1. `subagent_type` distinto de `analista-transacciones` → `SUBAGENTE_NO_PERMITIDO`.
  2. Sin cliente verificado → `SIN_IDENTIDAD` (misma razón del #9).
  3. Bloque ausente, JSON inválido, campos faltantes o con formato inválido →
     `CONTEXTO_INCOMPLETO`, con la razón que nombra los campos a corregir (solo nombres de
     campo, nunca valores).
  4. `cliente_id` distinto del verificado → `CLIENTE_DISTINTO` (misma razón del #9).
  5. Cualquier excepción → `FALLA_CONTROL`.

  La negación se registra en `estado.negaciones` como las del #9.
- **Rationale**: la constitución pide garantías deterministas para la regla 1; el bloque
  estructurado se verifica sin interpretar texto libre, y la misma validación sirve de contrato
  para el subagente (sus instrucciones leen el bloque).
- **Alternatives considered**: confiar en el prompt (no garantiza nada); validar el texto
  libre con palabras (prohibido).

## R3. Reglas 1 y 2 en lo que hace el subagente (FR-005, FR-006)

- **Decision**:
  - Las consultas del subagente pasan por `antes_de_herramienta` (#9) sin cambios: el matcher
    por nombre completo las cubre y el estado (`cliente_verificado`) es el de la conversación.
    La sonda y el escenario `e2e` lo comprueban registrando `agent_id`.
  - El subagente no tiene `iniciar_disputa`, `bloquear_tarjeta` ni `escalar_a_analista`:
    regla 2 imposible por diseño en el subagente; en el principal sigue el control del #9.
- **Riesgo verificado en la sonda**: que la delegación no dispare `UserPromptSubmit` (vaciaría
  los pendientes del #10 a mitad de turno). Si lo disparara, `al_recibir_mensaje` ignora las
  entradas con `agent_id`.

## R4. Instrucciones y resultado del subagente (FR-007, FR-008)

- **Decision**:
  - `prompt_analista(politica)` arma el prompt de sistema del subagente con el umbral y los
    plazos de la `Politica` cargada (no escritos a mano): leer el bloque `<contexto>`,
    consultar los cobros de esa tarjeta y rango, y clasificar cada uno:
    - `fuera_de_politica` si su antigüedad supera el plazo (exterior si el país no es CO);
    - si no, `sobre_umbral` si el monto supera el umbral;
    - si no, `disputable`.
  - Respuesta en un bloque `<analisis>{json}</analisis>` con `transacciones` (lista de
    `transaccion_id`, `fecha`, `monto`, `clasificacion`, `razon`) y
    `montos_no_encontrados`. Si la consulta falla, `error` con una frase y lista vacía; nunca
    inventa transacciones.
  - Si los datos del core no cargaron (`politica` es `None`), no se registra el subagente ni
    la herramienta de delegación (falla cerrada).
- **Rationale**: la clasificación es orientativa (principio II la deja como instrucción
  verificada con la API); el formato estructurado facilita que el principal la use y que el
  escenario la compruebe.

## R5. Prompt del principal v5 (FR-009)

- Sección "Análisis con analista-transacciones": con el cliente verificado y cobros por
  analizar, delegar con el bloque `<contexto>` (formato exacto) antes de disputar; usar la
  clasificación para disputar lo disputable y escalar lo demás; los controles deciden siempre
  y una disputa negada se escala igual. No delegar sin verificación ni para otro cliente.
- `VERSION_PROMPT = "5"`. Los ejemplos y el test de separación del #10 no cambian.

## R6. Ajustes heredados del #10 (FR-010)

- (a) Texto de T006 en `specs/010-.../tasks.md`: `DISPUTA_EXISTENTE` en lugar de
  `TRANSACCION_YA_DISPUTADA`.
- (b) Tests de entradas mal formadas (`None`, `{}`) en `antes_de_terminar` y
  `al_recibir_mensaje`.
- (c) `al_recibir_mensaje` con `suppress(Exception)` como los demás callbacks.
