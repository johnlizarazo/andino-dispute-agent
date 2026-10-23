# Quickstart de validación: Guardrails de desarrollo

Escenarios que prueban la spec de punta a punta. Para los detalles, ver
[contracts/](contracts/).

## Prerrequisitos

- `uv sync` hecho; `GITHUB_PAT` visible.
- Sesión de Claude Code **reiniciada** después de configurar el plugin, aceptando la
  confianza de la carpeta.

## 0. Tests deterministas

`uv run pytest` incluye los tests de `plugins/`, que pasan. Entre ellos (SC-001, SC-002):

- Al menos 20 tarjetas válidas generadas al correr, con y sin separadores, todas detectadas.
- Al menos 20 casos legítimos sin falsos positivos.

## 1. El plugin carga (US6 · SC-006)

1. `claude plugin validate ./` y `claude plugin validate ./plugins/andino-guardrails` → sin
   errores.
2. En `/plugin`, `andino-guardrails@banco-andino` aparece instalado y habilitado.
3. Si la fuente `directory` no funciona: aplicar el fallback de
   [plugin-marketplace.md](contracts/plugin-marketplace.md) y repetir.

## 2. Datos con forma real (US1)

El texto de prueba lo genera un script en el momento, para no dejar literales.

1. Pedir al asistente que escriba en `tmp-prueba.txt` una tarjeta válida generada → se
   **bloquea**, con un mensaje enmascarado.
2. Pedir un documento generado (`CC` seguido de 8 dígitos aleatorios) → se **bloquea**.
3. Pedir `1250000`, `CC-FIC-0001` y una secuencia de 16 dígitos que no pasa Luhn → se
   **permiten**.
4. Borrar `tmp-prueba.txt`.

## 3. Spec-first (US2)

1. En la rama `003-guardrails-desarrollo`, que tiene spec, plan y tareas, pedir crear
   `src/agente_disputas/prueba_spec.py` → se **permite**. Borrarlo después.
2. En una rama local `998-sin-spec`, sin carpeta de spec, pedir lo mismo → se **bloquea**,
   indicando qué falta. Volver a la rama del ticket y borrar `998-sin-spec`.

## 4. Formato (US3)

1. Pedir crear `src/agente_disputas/prueba_formato.py` con código mal formateado → queda
   formateado.
2. Borrarlo.

## 5. Cumplimiento (US4 · SC-005)

1. Invocar `/andino-guardrails:revisar-cumplimiento` → `VEREDICTO: APROBADO`, con las reglas
   de negocio en "NO APLICA" y los tests en verde.
2. Si `agent:` falla con el nombre con espacio de nombres: aplicar el fallback de
   [cumplimiento.md](contracts/cumplimiento.md).
3. Incumplimiento sembrado: en una rama local desechable `997-prueba-cumplimiento`, agregar
   un test que falle → la skill devuelve `BLOQUEADO`, y `/abrir-pr` se detiene sin publicar.
   Borrar la rama.

## 6. Rules (US5)

1. Leer un `test_*.py` del plugin → la sesión recibe la rule de tests.
2. `src/core_bancario_mcp/` aún no tiene archivos de herramientas: se comprueba que la rule
   existe con su `paths`. Su efecto se observa en el issue #4.

## 7. CI (FR-007)

1. El PR de este ticket dispara `guardrails`, y el job pasa: valida el workflow en positivo.
2. Prueba negativa **local**, con el mismo comando que corre el job: un script genera en
   el momento un diff con una tarjeta válida por Luhn en una línea agregada, y
   `bloquear_pii.py --diff` sale con 1 y la reporta enmascarada.

   No se publica ninguna rama de prueba con datos con forma real: quedarían en el
   historial del repositorio público (principio III).
