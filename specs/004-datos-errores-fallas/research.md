# Research: Datos ficticios, contrato de errores e inyección de fallas

Fase 0 del plan. Fuentes: la API de `mcp` 1.30.0 instalada, verificada en el entorno del
proyecto (`FastMCP`, `run(transport="stdio")`, `list_tools`, `call_tool`); la constitución;
y los contratos de los issues #1 a #3.

## R1. Estructura del paquete `core_bancario_mcp`

- **Decision**: módulos pequeños, cada uno con su test al lado:

  | Módulo | Responsabilidad |
  |---|---|
  | `errores.py` | Contrato `ok`/`error`, tipos y regla de reintento |
  | `datos/*.json` | Clientes, tarjetas, transacciones y políticas ficticias |
  | `repositorio.py` | Carga y validación de los datos, fechas relativas, consulta por id |
  | `fallas.py` | Inyección de fallas transitorias por variable de entorno |
  | `servidor.py` | Instancia `FastMCP("core-bancario")`; las herramientas llegan en #5 a #7 |
  | `__main__.py` | Punto de entrada: `python -m core_bancario_mcp` |

- **Rationale**: los issues #5 a #7 agregan herramientas sobre estas piezas sin tocarlas, y
  el agente (#9) importa solo `repositorio`.
- **Alternatives considered**: un único `servidor.py`. Mezclaría datos, errores y fallas, y
  haría más difícil que el agente reutilice solo la consulta.

## R2. Contrato de errores

- **Decision**:
  - Funciones `exito(datos)` y `error(tipo, codigo, mensaje)` que devuelven `dict`.
  - El tipo es un `StrEnum` `TipoError` con los cuatro valores.
  - `reintentable` **se deriva del tipo** (`tipo == transitorio`); no es un parámetro.
  - Códigos en una clase de constantes: `FALLA_TRANSITORIA`, `NO_ENCONTRADO`, etc.
- **Rationale**: derivar `reintentable` hace imposible por diseño un error de validación
  marcado como reintentable (FR-003), en línea con el principio II. Devolver `dict` es lo que
  FastMCP serializa como JSON (verificado).
- **Alternatives considered**:
  - Excepciones propias capturadas por un decorador: más indirección para el mismo resultado.
  - Pasar `reintentable` como parámetro: permitiría combinaciones inválidas.

## R3. Datos ficticios en JSON

- **Decision**: cuatro archivos en `src/core_bancario_mcp/datos/` (`clientes.json`,
  `tarjetas.json`, `transacciones.json`, `politicas.json`), leídos con `importlib.resources`.
  - Las transacciones guardan `dias_atras` en lugar de una fecha.
  - Las tarjetas guardan solo `ultimos4`.
  - Los documentos usan el formato `CC-FIC-NNNN`.
- **Rationale**:
  - Son legibles en la sustentación y fáciles de revisar en un diff.
  - El hook `bloquear_pii` y el CI los revisan al escribirlos.
  - `importlib.resources` funciona igual con el paquete instalado o en desarrollo.
- **Alternatives considered**:
  - SQLite: el enunciado dice que no hace falta una base de datos.
  - Datos en un módulo Python: mezclaría datos con código y se lee peor.

## R4. Fechas relativas y "hoy" inyectable

- **Decision**: `Repositorio(hoy: date | None = None)`. Si no se pasa, usa `date.today()`.
  `fecha = hoy - timedelta(days=dias_atras)` se calcula una vez al cargar.
- **Rationale**: los tests fijan "hoy" (por ejemplo, el 1 de enero) y verifican los bordes de
  mes y año (SC-001). Es la convención de la rule `tests.md`: sin reloj real.

## R5. Validación al cargar

- **Decision**: al construir el repositorio se valida:
  - Que estén los campos obligatorios de cada entidad.
  - Que `ultimos4` tenga exactamente 4 dígitos.
  - Que el documento cumpla `^CC-FIC-\d{4}$`.
  - Que no haya identificadores duplicados ni referencias rotas (tarjeta sin cliente,
    transacción sin tarjeta).

  Cualquier error lanza `DatosInvalidosError` con un mensaje que nombra el archivo y el
  registro.
- **Rationale**: FR-012. Un dato mal escrito falla al arrancar, no en medio de una demo.

## R6. Inyección de fallas

- **Decision**:
  - Variable `CORE_BANCARIO_FALLAS="operacion:N[,operacion:N]"`, por ejemplo
    `consultar_transacciones:2`.
  - `fallas.py` la interpreta al arrancar. Si el formato es inválido o N no es positivo,
    lanza `ConfiguracionFallasError`.
  - Expone un decorador `con_fallas(nombre)`: si a esa operación le quedan fallas,
    descuenta una y devuelve `error(transitorio, "FALLA_TRANSITORIA", ...)` sin ejecutarla.
  - El contador vive en el proceso del servidor.
- **Rationale**: es determinista (SC-002) y se aplica por nombre a cualquier herramienta
  futura (FR-016). Un decorador deja las herramientas limpias.
- **Alternatives considered**:
  - Fallas aleatorias por probabilidad: no son reproducibles.
  - Un parámetro en cada herramienta: contamina la interfaz que ve el modelo.

## R7. Consulta reutilizable por el agente

- **Decision**: el agente (#9) importa `core_bancario_mcp.repositorio` y llama a
  `Repositorio().obtener_transaccion(id)`, que devuelve un objeto `Transaccion` o `None`.
- **Rationale**:
  - El hook del umbral necesita el monto real con baja latencia y sin depender de que el
    servidor responda.
  - El monto y el titular de una transacción son **inmutables** en los datos, así que no
    importa que el agente y el servidor corran en procesos distintos.
  - Si la consulta falla, el hook falla cerrado (principio II).
- **Alternatives considered**: consultar vía una herramienta MCP. Haría depender la garantía
  del modelo o del transporte, y la falla transitoria inyectada bloquearía también el hook.
  Se descarta.
- **Límite declarado**: el estado mutable (disputas abiertas, tarjetas bloqueadas por el
  agente) vive solo en memoria del servidor. El hook del umbral no lo necesita.

## R8. Registro en `.mcp.json`

- **Decision**: agregar
  `"core-bancario": {"type": "stdio", "command": "uv", "args": ["run", "--no-sync", "python",
  "-m", "core_bancario_mcp"]}`.
- **Rationale**:
  - Sin credenciales (principio III).
  - `--no-sync` evita reinstalar el proyecto en cada arranque y el bloqueo de `.venv`
    observado en Windows.
  - Claude Code lanza el servidor con la raíz del proyecto como directorio de trabajo.

## R9. Ajustes heredados del #3

- **Rule de MCP**: queda "reintentable solo para `transitorio`", ahora respaldado por FR-003
  y por el contrato de errores. Se cita el contrato en la rule.
- **Test 4-6-5**: un helper que genera una tarjeta válida de 15 dígitos y la agrupa en 4-6-5.
- **`/dev/null` en `--diff`**: el modo diff deja de contar hallazgos cuando el destino es
  `/dev/null`. En un archivo borrado, git solo produce líneas `-`, así que la etiqueta no
  debería aparecer; se agrega un test que lo demuestra y se omite el archivo explícitamente.
