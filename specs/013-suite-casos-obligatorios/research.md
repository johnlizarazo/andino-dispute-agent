# Research: Suite de casos obligatorios y README

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

## R1. Cómo se registra lo que hizo el agente

- **Decision**: un ayudante de prueba, `tests/escenarios/registro.py`, conversa con el agente
  real (`ClaudeSDKClient` con `crear_opciones(entorno, controles)` y unos `Controles` propios)
  y arma un **registro de operaciones**: por cada `ToolUseBlock` del agente principal, su
  nombre, argumentos y, al llegar su `ToolResultBlock`, la respuesta leída con
  `controles.leer_respuesta`. Cada llamada se marca como negada si su `tool_use_id` está en
  `controles.estado.negaciones` (campo agregado en el #12). Al final se exponen también los
  pendientes de escalar (`controles.estado.pendientes`). El registro se construye con funciones
  puras sobre los mensajes del SDK y se prueba de forma determinista (`test_registro.py`).
- **Rationale**: FR-003 exige comprobar lo que se hizo, no lo que se dijo. Es el mismo
  emparejamiento por `tool_use_id` que ya funciona en `eventos.py` (verificado con la API en el
  #12), pero aquí hace falta el detalle (argumentos, códigos del core, orden) que los eventos
  resumen en lenguaje de negocio.
- **Alternatives considered**: reutilizar `LectorEventos` (pierde argumentos y códigos, y
  omite las lecturas, que el caso de homónimos necesita); espiar los callbacks de los hooks
  como en `test_delegacion_e2e.py` (solo ve las operaciones sobre productos, no
  `buscar_cliente` ni `escalar_a_analista`); usar `ResultadoTurno.herramientas` (solo nombres,
  sin resultados).

## R2. Un test por caso, en un solo archivo

- **Decision**: `tests/escenarios/test_casos_obligatorios.py` con seis funciones, una por
  caso, nombradas `test_caso_1_mensaje_de_ejemplo`, …, `test_caso_6_fuera_de_politica`. Los
  mensajes viven en `tests/escenarios/casos.py` (un diccionario por caso) para que el test de
  mensajes (R4) los compare sin importar un módulo de tests. El caso 5 hace dos conversaciones
  dentro de la misma función: falla pasajera (`buscar_cliente:1`) y persistente
  (`buscar_cliente:5`).
- **Rationale**: FR-001 pide exactamente un test por caso y un nombre que lo identifique; un
  solo archivo hace evidente que la suite es la dueña de los casos (FR-007).
- **Alternatives considered**: un archivo por caso (más piezas sin ganancia); parametrizar
  un solo test (los casos verifican cosas distintas y el nombre perdería claridad).

## R3. Qué comprueba cada caso (tolerando caminos válidos)

- **Decision**: cada caso afirma sobre el registro y el estado de los controles; ver
  [contracts/casos.md](contracts/casos.md). Donde el agente puede llegar por más de un camino
  válido, el test acepta todos los que cumplen la regla:
  - Caso 1: la disputa de `TRX-002` puede intentarse y ser negada por umbral, o no intentarse
    porque el subagente (#11) ya la clasificó como sobre umbral; en ambos casos nunca se abre,
    y siempre hay un escalamiento exitoso con causa `umbral` que incluye `TRX-002`.
  - Caso 6: la disputa de `TRX-006` puede intentarse y ser rechazada por el core con
    `FUERA_DE_POLITICA`, o no intentarse por la clasificación del subagente; nunca se abre ni
    se repite tras el rechazo, y siempre hay un escalamiento con causa `fuera_de_politica`.
- **Rationale**: la delegación del #11 hace que el agente pueda saltarse una disputa que sabe
  que no procede; exigir el intento haría fallar la suite por un comportamiento correcto.
  El escenario 7 de la US1 se ajustó en el punto de control 2 para aceptar los dos caminos.
- **Alternatives considered**: exigir el camino del ejemplo del prompt (frágil frente a la
  delegación); comprobar el texto de la respuesta (prohibido por FR-003).

## R4. Comprobación determinista de que los mensajes no están en el prompt

- **Decision**: `tests/escenarios/test_mensajes.py` (sin marca `e2e`, corre en
  `uv run pytest`): normaliza (minúsculas, sin tildes ni signos, espacios simples) cada mensaje
  de `casos.py` y cada ejemplo `Cliente: "..."` del `PROMPT_SISTEMA`, y afirma que ningún
  mensaje contiene un ejemplo ni es contenido por el prompt; además, que no comparten una
  secuencia de 8 palabras seguidas.
- **Rationale**: FR-006 y SC-002; el test sigue vigilando aunque el prompt cambie de versión
  (US3-2). La ventana de 8 palabras detecta copias parciales sin prohibir vocabulario común
  ("tarjeta terminada en").
- **Alternatives considered**: solo igualdad exacta (no detecta copias con un cambio menor);
  similitud difusa (umbral arbitrario y difícil de explicar).

## R5. Consolidación de escenarios existentes (FR-007)

- **Decision**: los dos tests de falla transitoria de `test_conversacion_e2e.py` pasan a ser
  el caso 5 de la suite y se eliminan de ese archivo. El test de ese archivo que prueba la
  regla 1 sin prompt de sistema se mantiene (verifica el principio II, no el caso
  obligatorio). `test_delegacion_e2e.py` y `test_eventos_e2e.py` se mantienen: prueban la
  delegación y los eventos de la interfaz.
- **Rationale**: un solo dueño por caso obligatorio, sin perder escenarios que prueban otra
  cosa.
- **Alternatives considered**: dejar los duplicados (dos fuentes de verdad para el mismo
  caso); mover todos los escenarios a la suite (mezcla responsabilidades de otros tickets).

## R6. Datos y mensajes de cada caso

- **Decision**: los datos de verificación se leen en tiempo de ejecución de
  `Repositorio().clientes[...]`. Clientes: caso 1 `CLI-001` (4821, `TRX-001`/`TRX-002`); caso 3
  el nombre compartido por `CLI-002` y `CLI-003`; caso 4 sin identificarse, pidiendo disputar
  un cobro; caso 5 `CLI-002` por documento; caso 6 `CLI-004` (3344, `TRX-006`). Cada caso entra
  en un turno con todo lo necesario; si el agente pide un dato que el mensaje ya trae, el
  escenario no responde de nuevo (el test falla y señala una regresión).
- **Rationale**: FR-012 y la convención de no escribir datos de verificación como literales.
  Un turno por caso mantiene la suite rápida (SC-005) y determinista en su guion.
- **Alternatives considered**: conversaciones de varios turnos con respuestas condicionales
  (el guion dependería de la redacción del modelo).

## R7. README

- **Decision**: reorganizar el README en: inicio rápido (5 minutos) con pestañas o bloques
  para PowerShell y para bash/zsh (definir `ANTHROPIC_API_KEY` solo para la sesión,
  `uv sync`, `uv run pytest`, `uv run andino-chat`, `uv run python -m agente_disputas`);
  escenarios (`uv run pytest -m e2e`, duración y consumo de API); tabla de los seis casos con
  su test y un mensaje para el chat; Project y video (ya existen, se conservan). Las secciones
  de token de GitHub, convenciones y guardrails se mantienen después, para quien desarrolla.
- **Rationale**: FR-009 a FR-011 y SC-004; quien evalúa lee primero lo que necesita para
  correr el proyecto.
- **Alternatives considered**: un documento aparte (`docs/`) para la evaluación (otro archivo
  que mantener; el issue pide el README).
