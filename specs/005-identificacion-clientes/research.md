# Research: Identificación (issue #5)

API verificada contra `mcp` 1.30.0 instalado (`FastMCP.tool`, `add_tool`, `list_tools`,
`call_tool`) con pruebas rápidas en el entorno del proyecto.

## R1. Acceso de las herramientas al repositorio y al inyector (FR-016)

- **Decision**: un `Contexto` explícito (dataclass con `repositorio`, `inyector` e
  `intentos`) que `crear_servidor` construye y pasa a `registrar(servidor, contexto)` de
  cada módulo de herramientas. Las herramientas registradas son cierres que delegan en
  funciones puras `buscar_cliente(contexto, ...)` y `verificar_identidad(contexto, ...)`.
  `crear_servidor` conserva su firma actual y deja de colgar atributos en `FastMCP`.
- **Rationale**: es lo más simple que queda explícito y tipado. Los tests llaman a las
  funciones puras con un `Contexto` armado a mano (deterministas, sin servidor) y prueban el
  registro con `list_tools`/`call_tool`. Verificado: el decorador `con_fallas` aplicado
  debajo de `@servidor.tool` conserva la firma (FastMCP la lee por `__wrapped__`) y el
  esquema de entrada se publica bien.
- **Alternatives considered**:
  - `lifespan` + `Context` inyectado: el estado solo existe durante una sesión del servidor
    y cada herramienta recibiría un parámetro `ctx`; los tests necesitarían levantar el
    `lifespan` o simular `Context`. Más piezas sin beneficio aquí.
  - Subclase de `FastMCP` con atributos declarados: acopla las herramientas a la clase del
    framework.
  - Variables de módulo (singleton): estado global, tests acoplados entre sí.

## R2. Inyección de fallas en las herramientas (FR-012)

- **Decision**: `registrar` envuelve cada herramienta con
  `con_fallas(contexto.inyector, "<nombre de la herramienta>")`. La falla se evalúa antes
  de validar o consultar: simula que el core no respondió. Una falla transitoria **no**
  cuenta como intento de verificación.
- **Rationale**: reutiliza el decorador del #4 sin cambios; el nombre de la operación es el
  de la herramienta, como documenta `fallas.py`.

## R3. Contador de intentos fallidos (FR-009, FR-010)

- **Decision**: clase `IntentosVerificacion` en `contexto.py`, con un `dict[str, int]` por
  `cliente_id`, `MAXIMO = 3`, y métodos `agotados(cliente_id)`, `registrar_fallo(cliente_id)`
  y `reiniciar(cliente_id)`. Vive en el `Contexto`, es decir, en memoria del proceso.
- Orden en `verificar_identidad`: parámetros → cliente existe (si no, validación, sin
  contar) → ¿agotados? (negocio `INTENTOS_AGOTADOS`) → comparar dato (éxito reinicia; fallo
  suma y responde permiso `VERIFICACION_FALLIDA`). El tercer fallo responde permiso; desde
  el cuarto intento, negocio, aunque el dato sea correcto.
- **Rationale**: el límite protege al cliente (no a una conversación), por eso se cuenta por
  cliente y no por sesión; el core no sabe de sesiones (FR-010). Reiniciar con el proceso es
  suficiente para la demo (supuesto aprobado en la spec).
- **Alternatives considered**: persistir en disco (estado mutable fuera de memoria, nada que
  ganar en la demo); contar en el agente (el agente es justo lo que se quiere acotar).

## R4. Normalización de nombres y validación de criterios (FR-001, FR-004, FR-005)

- **Decision**:
  - `_normalizar(texto)`: `unicodedata.normalize("NFKD")`, quitar marcas combinantes
    (`unicodedata.combining`), `casefold()` y extraer las palabras con
    `re.findall(r"\w+")` (ajuste U1: la puntuación no se pega a la palabra, "Pérez,"
    coincide). "Pérez", "PEREZ" y "perez" quedan iguales (también "ñ" → "n").
  - **Nombre**: coincide si cada palabra buscada es una palabra completa del nombre
    normalizado (no subcadena: "an" no debe encontrar "Andrés"). Rechazo por validación si
    tras normalizar quedan menos de 2 letras o el texto supera 100 caracteres.
  - **Documento**: `^CC-FIC-[0-9]{4}$` tras quitar espacios en los extremos.
  - **Últimos 4**: `^[0-9]{4}$`. Devuelve todos los titulares distintos de tarjetas con esos
    dígitos, sin repetir cliente, ordenados por id.
  - **Exactamente un criterio**: los tres parámetros son opcionales; se cuentan los que no
    son `None` ni texto vacío o de solo espacios. Cero o más de uno → `PARAMETRO_INVALIDO`.
    Un valor que no es texto también es `PARAMETRO_INVALIDO` (R5).
- **Rationale**: `[0-9]` en lugar de `\d` evita aceptar dígitos no ASCII; coincidencia por
  palabras completas cumple FR-004 sin falsos positivos. El orden por id hace las respuestas
  deterministas.

## R5. Errores de tipo fuera del contrato

- **Hallazgo**: con parámetros tipados como `str`, FastMCP valida los argumentos con pydantic antes de llamar a la herramienta.
  Un valor de tipo JSON incorrecto (p. ej. `ultimos4: 4821` como número) o un parámetro
  obligatorio ausente se responden como error de protocolo (`isError: true`, texto libre),
  no con el contrato.
- **Decision** (ajuste C1 del análisis): todos los parámetros usan el tipo
  `Texto = Annotated[object, WithJsonSchema({"type": "string"})]` con valor por defecto
  `None`. El esquema publicado sigue diciendo "texto" (la mejor prevención para el modelo),
  pero pydantic deja pasar cualquier valor y la herramienta valida `isinstance(valor, str)`:
  ausencia, vacío, número, lista u objeto se responden con el contrato
  (`PARAMETRO_INVALIDO`). Ninguna respuesta queda fuera del principio V. Verificado en el
  entorno con nada, un número, una lista y un texto.
- **Alternatives considered**: `str | None` (un tipo JSON incorrecto quedaba como error de
  protocolo de FastMCP, fuera del contrato: lo marcó `/speckit-analyze` como CRITICAL);
  `Any` sin esquema (el modelo pierde la indicación de que son textos); interceptar la
  validación de FastMCP (depende de internos del framework).

## R6. Comparación del dato de verificación (FR-006, FR-007)

- **Decision**: el parámetro se llama `dato_verificacion`, como el campo de los datos
  (ajuste I1). `hmac.compare_digest(dato_verificacion, cliente.dato_verificacion)` sin
  normalizar (coincidencia exacta). El mensaje de error no incluye el dato esperado ni pistas.
- **Rationale**: una línea, tiempo constante; evita filtrar por tiempos aunque sea una demo.
- **Ajuste del #6**: se recortan los espacios de los extremos de `cliente_id` y
  `dato_verificacion`, como en `buscar_cliente`; la comparación sigue exacta tras recortar.

## R7. Endurecimiento de datos y fallas (FR-014, FR-015)

- **Datos**: cada archivo debe ser una lista de objetos (`politicas.json`, un objeto). Tipos
  por campo: textos no vacíos para ids, nombre, comercio y estado; enteros (`int` y no
  `bool`) para `monto`, `dias_atras` y los campos de la política. `estado` de tarjeta en
  {`activa`, `bloqueada`}; `pais` `^[A-Z]{2}$`; `dato_verificacion` `^[0-9]{4}$`; todos los
  patrones con `[0-9]`. Todo error es `DatosInvalidosError` con archivo y registro.
- **Fallas**: operación `^[a-z0-9_]+$`, veces `^[0-9]+$` (ASCII, sin signos) y `>= 1`;
  operación repetida → `ConfiguracionFallasError`.
- **Rationale**: son los no bloqueantes de la revisión del #4; hoy un tipo incorrecto puede
  terminar en `TypeError` con traza en vez de un mensaje claro (SC-005).
