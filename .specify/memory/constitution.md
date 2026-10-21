# Constitución de Andino Dispute Agent

Agente de primer contacto para disputas de transacciones y contracargos de Banco Andino
(banco ficticio), construido con Claude Agent SDK (Python 3.14, `uv`) y un servidor MCP
propio, `core-bancario`, que simula el core bancario con datos ficticios.

## Core Principles

### I. Reglas de negocio del banco (no negociables)

1. **Identidad verificada.** Ninguna operación sobre productos del cliente ocurre sin
   identidad verificada, y esa identidad DEBE corresponder al titular del producto o de la
   transacción. Exentas: `buscar_cliente`, `verificar_identidad` y `escalar_a_analista`.
   Bloquear una tarjeta SÍ exige identidad verificada.
2. **Umbral de disputa.** Una disputa de hasta $500.000 (inclusive) se inicia
   automáticamente; por encima requiere un analista humano. El monto DEBE obtenerse del core
   por el identificador de la transacción, nunca del argumento que envía el modelo.
3. **Bloqueo inmediato.** El bloqueo de tarjeta por sospecha de fraude es inmediato y no
   requiere aprobación de un analista (sí identidad verificada, por la regla 1).
4. **Persona a pedido.** Si el cliente pide explícitamente hablar con una persona, se escala
   de inmediato, sin investigar primero.
5. **Fuera de política, se escala.** Si la política del banco no cubre el caso (p. ej., un
   cobro de un comercio en el exterior con más de 90 días), el agente escala en lugar de
   improvisar.

Los montos son pesos colombianos ficticios. Los umbrales no se negocian.

### II. Garantías deterministas antes que instrucciones

Lo que no puede fallar se hace cumplir con mecanismos deterministas: hooks del Agent SDK,
permisos y hooks de Claude Code, y validaciones del servidor MCP. El prompt orienta el
comportamiento, pero NUNCA es la única garantía de una regla.

- Las reglas 1 y 2 se garantizan con hooks `PreToolUse` del Agent SDK que niegan la
  operación con una razón explicativa y fallan cerrado: si no se puede consultar el dato
  necesario para decidir, se niega.
- El diseño de herramientas hace imposible el resultado prohibido de las reglas 3 y 5:
  `bloquear_tarjeta` no admite aprobación intermedia, y el servidor rechaza con error de
  negocio no reintentable la disputa que la política no cubre.
- La obligación de escalar tras una disputa negada por umbral o rechazada por política se
  garantiza con un hook `Stop` sobre el estado de la sesión: el agente no puede cerrar el
  turno con un escalamiento pendiente. El hook tiene un tope de reintentos para no forzar
  un ciclo sin salida si el escalamiento falla.
- Lo que exige interpretar al cliente (reconocer que pide una persona, regla 4) se orienta
  con instrucciones, ejemplos positivos y negativos en el prompt y descripciones de
  herramientas, y se verifica con tests de escenario. No se detecta con palabras clave.
- Toda regla nueva DEBE declarar en su spec si se garantiza con hook o con instrucción, y
  por qué.

Razón: una regla que depende solo del prompt puede omitirse; un hook no. Cada regla queda
en uno de tres niveles: imposible por diseño, garantizada por hook, u orientada y
verificada por test.

### III. Datos exclusivamente ficticios y cero credenciales

- Ningún dato real de clientes, cuentas o tarjetas, ni en código, tests, logs,
  configuración ni documentación.
- Tarjetas solo como últimos 4 dígitos; documentos con formato no real (`CC-FIC-0001`).
- Los valores que deban pasar Luhn en tests se generan en tiempo de ejecución, nunca como
  literales.
- Ninguna credencial en el repositorio. Los secretos se leen solo de variables de entorno;
  los archivos `.env*` quedan fuera de git y fuera del alcance de Claude Code.

Razón: el repositorio es público y un dato que parezca real o una credencial es falta grave.

### IV. Spec-first

- No se escribe código de producción de un ticket sin `spec.md`, `plan.md` y `tasks.md`
  en `specs/<rama>/`.
- Cada ticket nace de un issue de GitHub; su `spec.md` enlaza el issue (`Issue: #N`) y su
  pull request lo cierra (`Closes #N`).
- La constitución es la excepción: es insumo de Spec Kit, no producto de un ticket.

### V. Contrato de herramientas y errores estructurados

- Toda herramienta MCP responde `{"ok": true, "datos": ...}` o
  `{"ok": false, "error": {"tipo", "codigo", "mensaje", "reintentable"}}`, con `tipo` en
  `transitorio`, `validacion`, `negocio` o `permiso`.
- Una búsqueda sin resultados NO es error: responde `ok: true` con una lista vacía.
- Las descripciones de herramientas DEBEN dejar claro cuándo usar cada una: buscar no
  verifica identidad, y con varias coincidencias se pide otro identificador; nunca se elige.

Razón: el agente decide si reintenta, escala o pregunta a partir de la estructura del error,
no de interpretar texto.

### VI. Tests junto al código, en dos niveles

- Los tests unitarios viven junto al módulo que prueban (`test_*.py` en la misma carpeta) y
  siguen las mismas convenciones en todas las carpetas.
- **Nivel determinista:** hooks y herramientas MCP, sin llamadas a la API. Corre con
  `uv run pytest` y DEBE estar siempre en verde.
- **Nivel de escenario:** casos obligatorios de punta a punta, marcados `e2e`; llaman al
  modelo y requieren `ANTHROPIC_API_KEY`. Corren con `uv run pytest -m e2e`.
- Los mensajes de los tests de escenario DEBEN ser distintos de los ejemplos del prompt de
  sistema, para que un test no pase por memoria.

### VII. Simplicidad y trazabilidad

- Pocas piezas, bien ubicadas y justificadas; nada decorativo. Toda pieza del ecosistema
  de Claude Code resuelve una necesidad concreta y su justificación queda en `DECISIONES.md`.
- El avance del proyecto DEBE poder reconstruirse solo mirando GitHub: issues, pull
  requests y Project.

## Restricciones técnicas y de seguridad

- **Stack:** Python 3.14 con `uv`; `claude-agent-sdk` para el agente; FastMCP por stdio
  para `core-bancario`; Chainlit para la interfaz de chat; `pytest` y `ruff` en desarrollo.
- **Paquetes:** `agente_disputas` (agente) y `core_bancario_mcp` (servidor), ambos bajo
  `src/`.
- **Nombres de herramientas MCP en español:** `buscar_cliente`, `verificar_identidad`,
  `consultar_transacciones`, `iniciar_disputa`, `bloquear_tarjeta`, `escalar_a_analista`.
- **Configuración compartida vs. personal:** las convenciones del equipo viven en archivos
  versionados (`CLAUDE.md`, `.claude/settings.json`, `.mcp.json`, plugin); lo personal en
  `CLAUDE.local.md`, `.claude/settings.local.json` o `~/.claude/`, nunca versionado.
- **Servidores MCP:** `.mcp.json` solo referencia variables de entorno (p. ej.
  `${GITHUB_PAT}`), nunca valores.

## Flujo de desarrollo y puntos de control

1. Se toma el siguiente issue del Project; pasa a *In Progress* y se lanza
   `/speckit-specify` con su contenido.
2. **Punto de control humano:** se revisa `spec.md` y se decide si hace falta
   `/speckit-clarify`.
3. `/speckit-plan`. **Punto de control humano:** se revisa `plan.md`.
4. `/speckit-tasks` y `/speckit-analyze`. **Punto de control humano:** se revisa el
   resultado de `analyze` antes de implementar.
5. `/speckit-implement` (y `/speckit-converge` si quedan brechas).
6. Antes del pull request: revisión independiente del código y revisión de cumplimiento de
   los principios I a III. Un hallazgo bloqueante detiene el pull request.
7. El pull request pasa el issue a *In Review*; el merge es la aprobación final y lo pasa a
   *Done*.

Los ajustes hechos en cada punto de control se registran en un comentario del issue.

## Governance

- Esta constitución prevalece sobre specs, planes y cualquier otra práctica del proyecto.
- Las enmiendas se hacen por pull request con `/speckit-constitution` y explican el cambio.
- Versionado semántico: MAJOR si se elimina o redefine un principio; MINOR si se agrega un
  principio o sección o se amplía materialmente; PATCH para aclaraciones y redacción.
- Cumplimiento: el subagente `auditor-cumplimiento` verifica los principios I a III antes de
  cada pull request; los revisores pueden bloquear cualquier cambio que los incumpla.
- La guía operativa para Claude Code vive en `CLAUDE.md`, que importa esta constitución.

**Version**: 1.0.0 | **Ratified**: 2026-10-20 | **Last Amended**: 2026-10-20
