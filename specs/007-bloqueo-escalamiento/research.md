# Research: Bloqueo y escalamiento (issue #7)

Verificado en el entorno del proyecto (Python 3.14, `mcp` 1.30.0, `pydantic`).

## R1. Módulo y registros (FR-003, FR-004, FR-010)

- **Decision**: `bloqueo_escalamiento.py` con funciones puras `bloquear_tarjeta(contexto,
  ...)` y `escalar_a_analista(contexto, ...)` y `registrar(servidor, contexto)`. En
  `contexto.py`:
  - `RegistroBloqueos`: conjunto de `tarjeta_id` bloqueadas en la sesión y su motivo.
    `estado_de(tarjeta) -> "activa" | "bloqueada"` (bloqueada si `tarjeta.estado ==
    "bloqueada"` o si está en el conjunto). `bloquear(tarjeta, motivo) -> bool`: devuelve si
    ya estaba bloqueada antes del llamado; nunca desbloquea.
  - `Escalamiento` (dataclass inmutable, con el detalle para el analista) y
    `RegistroEscalamientos` con contador propio: `registrar(...) -> Escalamiento` con
    `ESC-0001`, `ESC-0002`, ...; `todos()` sirve a los tests y a la vista del analista. El
    hook `Stop` del #10 corre en el proceso del agente y no lee esta memoria: se basa en las
    respuestas de las herramientas (ajuste I1).
  - Campos nuevos del `Contexto`: `bloqueos` y `escalamientos`, con `default_factory`.
- **Rationale**: misma convención que intentos y disputas; las tarjetas del repositorio son
  inmutables y las comparte el hook del #9.
- **Alternatives considered**: mutar `Tarjeta.estado` (dataclass inmutable, compartida entre
  procesos); persistir en disco (nada que ganar en la demo).

## R2. Bloqueo (FR-001 a FR-003)

- **Decision**: parámetros `cliente_id`, `ultimos4`, `motivo` (todos `Texto`). Orden:
  falla inyectada → tipos y vacíos (recortados) → `ultimos4` "`^[0-9]{4}$`" → motivo hasta
  500 caracteres → `repositorio.tarjetas_de(...)` vacío → `NO_ENCONTRADO` (mismo mensaje que
  en `consultar_transacciones`) → bloquear todas las tarjetas devueltas → `exito({"ultimos4",
  "estado": "bloqueada", "ya_estaba_bloqueada"})`. `ya_estaba_bloqueada` es verdadero solo si
  **todas** las tarjetas ya lo estaban.
- **Rationale**: un bloqueo repetido es idempotente y no es un error (criterio del issue);
  el agente puede informarlo al cliente.

## R3. Lista de transacciones y contrato (FR-008, FR-013)

- **Decision**: tipo `ListaTexto = Annotated[object, WithJsonSchema({"type": "array",
  "items": {"type": "string"}})]`, junto a `Texto` en `identificacion.py`. Verificado: el
  esquema publica `array` de `string` y FastMCP deja pasar `None`, una lista, un texto o una
  lista con otros tipos hasta la herramienta.
- La herramienta acepta: `None` (sin transacciones), una lista de textos, o un texto que sea
  una lista JSON de textos (algunos clientes MCP envían así los arreglos). Cualquier otra cosa
  (número, objeto, lista con no-textos, texto que no es lista JSON) → `PARAMETRO_INVALIDO`.
  Los ids se recortan y se deduplican conservando el orden.
- **Alternatives considered**: un texto separado por comas (el esquema no le dice al modelo
  que es una lista); `list[str]` de pydantic (un tipo incorrecto sale como error de FastMCP,
  fuera del contrato: el mismo problema que resolvió `Texto` en el #5).

## R4. Validación del resumen y orden de evaluación (FR-005 a FR-011)

- **Decision**: parámetros `causa`, `cliente_id`, `transacciones` (`ListaTexto`),
  `acciones_realizadas` y `accion_recomendada`. Causas válidas: `persona_solicitada`,
  `umbral`, `fuera_de_politica`, `intentos_agotados`, `otra`. Orden:
  1. Falla inyectada (no registra nada).
  2. Tipos: textos o `None`; transacciones según R3 → `PARAMETRO_INVALIDO`.
  3. Obligatorios: `causa`, `acciones_realizadas`, `accion_recomendada` (no vacíos tras
     recortar); un solo error que nombra **todos** los faltantes.
  4. `causa` fuera de la lista → `PARAMETRO_INVALIDO` con las causas válidas.
  5. Largos: acciones hasta 1000 caracteres; acción recomendada hasta 500.
  6. Cliente: obligatorio salvo `persona_solicitada`; si se indica y no existe →
     `NO_ENCONTRADO`.
  7. Transacciones: obligatorias y no vacías con `umbral` y `fuera_de_politica`; cada una
     debe existir (`NO_ENCONTRADO`) y, si hay cliente, pertenecerle (`PARAMETRO_INVALIDO`).
  8. Registrar y responder `exito(resumen)`.
- **Rationale**: el analista recibe siempre los seis elementos del handoff; la regla 4 no se
  frena (persona solicitada sin cliente ni transacciones).

## R5. Resumen registrado y respuesta al agente (FR-009, FR-010, FR-010b)

- **Decision** (ajuste C1 del análisis): el core **registra** para el analista un
  `Escalamiento` con el resumen completo (cliente con nombre; transacciones con fecha, monto,
  comercio y caso de disputa tomados del repositorio y del registro de disputas; total;
  acciones; recomendación; estado `pendiente_analista`). Al agente le **responde** solo
  `{"escalamiento_id", "causa", "estado", "cantidad_transacciones"}`.
- **Rationale**: `escalar_a_analista` está exenta de identidad verificada (regla 1); si su
  respuesta devolviera montos, fechas o comercios, sería un camino para consultar productos
  sin verificación (con un `cliente_id` y unos `TRX-NNN` adivinables), justo en el caso
  `intentos_agotados`. El agente solo necesita el identificador para informar al cliente; el
  analista lee el registro.
- **Alternatives considered**: devolver el resumen completo (descartado por lo anterior);
  devolverlo solo si hubo verificación (el core no guarda sesiones de identidad, FR-010 del
  #5).

## R6. Ajustes heredados del #6 (US4)

- **(a)** `consultar_transacciones`: recortar cada fecha antes de decidir si se omite; un
  texto vacío o de solo espacios es omitido (hoy el de solo espacios da error).
- **(b)** `RegistroDisputas`: contador propio `self._ultimo` en lugar de `len(...) + 1`.
- **(c)** `Politica.limite_dias(transaccion) -> int` (nacional si `pais == "CO"`, exterior en
  otro caso); `cubre` y el mensaje de `FUERA_DE_POLITICA` lo usan.
