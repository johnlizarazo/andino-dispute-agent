# Research: Hooks del SDK para R1 y R2 (issue #9)

API verificada por introspección de `claude-agent-sdk` 0.2.168 instalado (`types.py`:
`HookMatcher`, `PreToolUseHookInput`, `PostToolUseHookInput`, `HookCallback`,
`PreToolUseHookSpecificOutput`).

## R1. API de hooks del SDK

- **Hallazgo**:
  - `ClaudeAgentOptions.hooks: dict[HookEvent, list[HookMatcher]]`.
  - `HookMatcher(matcher: str | None, hooks: list[HookCallback], timeout: float | None)`;
    `matcher` admite alternativas con `|` (sintaxis de Claude Code).
  - `HookCallback = async (input, tool_use_id, context) -> HookJSONOutput`.
  - `PreToolUse` recibe `tool_name` y `tool_input: dict`; niega con
    `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
    "permissionDecisionReason": "..."}}`. La razón llega al modelo como resultado de la
    herramienta, sin ejecutarla.
  - `PostToolUse` recibe además `tool_response: Any` (forma no tipada por el SDK).
  - Los hooks se ejecutan en el proceso del agente (Python), así que pueden leer estado propio
    de la conversación.
- **Decision**: un `HookMatcher` de `PreToolUse` con las 3 herramientas sobre productos por
  nombre completo (`mcp__core-bancario__consultar_transacciones|...iniciar_disputa|
  ...bloquear_tarjeta`) y un `HookMatcher` de `PostToolUse` sobre
  `mcp__core-bancario__verificar_identidad`. Un callback de `PreToolUse` que despacha por
  `tool_name`; un nombre inesperado dentro del callback se niega.
- **Rationale**: el nombre completo con el prefijo del servidor es lo que ve el CLI tanto en
  el agente principal como en un subagente (FR-008); no hay comodines que puedan cubrir de más
  o de menos.
- **Alternatives considered**: un matcher por herramienta (tres registros iguales, más ruido);
  `can_use_tool` (callback de permisos: con `dontAsk` y `allowed_tools` no se invoca para las
  herramientas preaprobadas, y la constitución exige hooks `PreToolUse`).

## R2. Falla cerrada (FR-007)

- **Hallazgo**: una excepción dentro del callback, o un tiempo de espera agotado, se reporta
  al CLI como error del hook; en Claude Code un error de hook no bloqueante deja seguir la
  herramienta. Es decir, sin protección propia el control fallaría **abierto**.
- **Decision**:
  - Cada callback de `PreToolUse` envuelve toda su lógica en `try/except Exception` y ante
    cualquier excepción niega con una razón genérica ("no se pudo confirmar la operación").
  - La lógica decide por lista blanca: solo autoriza si todas las comprobaciones pasan; todo
    camino no previsto termina en negación.
  - El callback es en memoria y rápido; `timeout` del matcher en 10 s, muy por encima de lo
    que tarda, para que nunca se agote en condiciones normales.
- **Rationale**: la constitución pide que el control niegue si no puede consultar el dato.
  La protección vive en nuestro código, no en el comportamiento del CLI ante errores.
- **Alternatives considered**: confiar en el manejo de errores del CLI (no documentado como
  bloqueante).

## R3. Estado de la conversación (FR-001, FR-002)

- **Decision**: `EstadoSesion` (dataclass mutable) con `cliente_verificado: str | None` y
  `negaciones: list[Negacion]` (herramienta, código de la razón). Lo crea `crear_opciones`
  por cada conversación y lo comparten los dos callbacks por clausura (`Controles`).
  - `cli.py` crea un `ClaudeSDKClient` por conversación con opciones nuevas, así que el estado
    nace vacío y muere con la conversación (FR-002).
  - `negaciones` sirve para que los tests (y el escenario sin prompt) comprueben que el control
    actuó; el #10 la reutilizará para el hook `Stop`.
- **Rationale**: el core no guarda sesiones de identidad (cada proceso del core es por
  conversación, pero el agente no debe depender de eso); el estado vive donde se toma la
  decisión.
- **Alternatives considered**: guardar el verificado en el core y consultarlo por MCP (otra
  herramienta, otra llamada y un punto de falla más); variable global (se compartiría entre
  conversaciones).

## R4. Registro del cliente verificado (PostToolUse)

- **Hallazgo**: `tool_response` para herramientas MCP no tiene forma documentada en el SDK; en
  Claude Code suele llegar como la lista de bloques de contenido del resultado MCP
  (`[{"type": "text", "text": "<json>"}]`), y FastMCP además adjunta contenido estructurado.
- **Decision**: `leer_respuesta(tool_response) -> dict | None` acepta, en este orden:
  1. un `dict` con la clave `ok` (el contrato del core);
  2. un `dict` con `structuredContent` (o `structured_content`) que sea ese contrato, o con
     `content` que sea una lista de bloques;
  3. una lista de bloques: el primer bloque `text` cuyo texto sea JSON con la clave `ok`;
  4. un `str` con ese JSON.

  Cualquier otra forma → `None`. Solo registra si la respuesta es
  `{"ok": true, "datos": {"verificado": true, "cliente_id": <texto no vacío>}}` y además
  `cliente_id` coincide con el `cliente_id` de `tool_input` (sin espacios). Si no, no toca el
  estado (una verificación fallida o ilegible no registra a nadie, ni borra al anterior).
- **Verificación empírica**: la tarea de verificación con la API registra la forma real de
  `tool_response` y se ajusta el lector si hiciera falta (quickstart §3).
- **Rationale**: ser tolerante con la forma no abre la puerta: solo un éxito explícito del
  core, para el mismo cliente pedido, registra; lo demás deja la conversación sin verificar.
- **Último verificado**: un nuevo éxito reemplaza al anterior (Assumptions de la spec).

## R5. Decisión del PreToolUse (FR-003, FR-004, FR-006)

Orden: identidad → titularidad → umbral. Razones en español, sin datos de otros clientes.

| Herramienta | Comprobación | Código de la negación |
|---|---|---|
| las 3 | no hay `cliente_verificado` | `SIN_IDENTIDAD` |
| `consultar_transacciones`, `bloquear_tarjeta` | `cliente_id` no es texto, o sin espacios no es el verificado | `CLIENTE_DISTINTO` |
| `iniciar_disputa` | `transaccion_id` no es texto, la transacción no existe o su titular no es el verificado | `TRANSACCION_NO_CONFIRMADA` (misma razón para las tres, para no permitir sondear ids) |
| `iniciar_disputa` | `Politica.requiere_analista(monto)` | `REQUIERE_ANALISTA` |
| las 3 | no se pudo cargar o consultar el dato, o excepción | `FALLA_CONTROL` |

- El monto y el titular se leen de `core_bancario_mcp.repositorio.Repositorio` por el
  `transaccion_id` del argumento, nunca de otro argumento (no existe parámetro `monto`).
- `Politica.requiere_analista` es la misma definición que usa el core (una sola fuente).
- Argumentos de más (p. ej. `monto` inventado) se ignoran: el core también los rechaza o ignora.

## R6. Datos del control y falla inyectable

- **Decision**: `Controles` recibe una función `buscar_transaccion(id) -> Transaccion | None`
  y la `Politica`. En producción (`Controles.desde_entorno(entorno)`):
  - Carga `Repositorio()` una vez al crear las opciones. Si la carga falla
    (`DatosInvalidosError` u otra), el control queda sin datos y niega toda disputa con
    `FALLA_CONTROL` (consultar y bloquear no necesitan el repositorio).
  - La falla inyectable reutiliza `InyectorFallas` del core con la **misma** variable
    `CORE_BANCARIO_FALLAS` y una operación propia, `control_transaccion`:
    `CORE_BANCARIO_FALLAS="control_transaccion:1"` hace que la primera consulta del control
    falle (excepción) y la disputa se niegue. El core ignora operaciones que no usa.
- **Rationale**: un solo mando de fallas para la demo; mismo mecanismo determinista ya probado.
- **Alternatives considered**: una variable nueva (`ANDINO_FALLAS_CONTROLES`): más
  configuración para el mismo fin.

## R7. Opciones del agente y prompt v3 (FR-009, FR-010)

- `crear_opciones(entorno, controles=None)`: si no recibe `controles`, los crea con
  `Controles.desde_entorno(entorno)`; agrega `hooks=controles.hooks()`.
- `allowed_tools` = las 6 herramientas; `disallowed_tools=[]`. Se elimina
  `HERRAMIENTAS_HABILITADAS`.
- **Sin prompt** (FR-009): los hooks no leen `system_prompt`. El test arma las opciones,
  reemplaza `system_prompt` por `None` con `dataclasses.replace` y ejecuta el callback
  `PreToolUse` registrado en `opciones.hooks` para una disputa sin verificación: se niega.
  Además, un escenario `e2e` sin prompt de sistema pide una disputa sin identificarse y
  comprueba que `negaciones` registra `SIN_IDENTIDAD` (o que `iniciar_disputa` nunca se pidió).
- **Prompt v3**: se quita "Disponibilidad actual"; se agrega una sección corta "Cuando una
  operación se niega": explicar al cliente sin detalles internos; si la razón pide verificar,
  verificar; si pide analista, escalar con la causa que corresponda. El hook es la garantía;
  el prompt solo orienta. `VERSION_PROMPT = "3"`.

## R8. Ajustes heredados del #8 (FR-011)

- (a) `escalar_a_analista` sin `cliente_id` y con `transacciones` → `PARAMETRO_INVALIDO`
  ("sin cliente no se indican transacciones"); se reemplaza
  `test_persona_solicitada_sin_cliente_acepta_transacciones` por su inverso.
- (b) Tests de `main()`: `KeyboardInterrupt` → despedida y código 0; `CLINotFoundError` →
  mensaje en stderr y código 1, sin traza (se simula `_ejecutar`).
- (c) T007 del #8: texto alineado con lo implementado (3 habilitadas en el #8).
- (d) `procesar_turno(mensajes: AsyncIterable[Message])`.
- (e) Líneas de más de 95 caracteres en `prompts.py` (la de "Disponibilidad actual"
  desaparece) y `cli.py` (líneas 40–41).
