# Implementation Plan: Plugin, marketplace y DECISIONES.md

**Branch**: `014-plugin-marketplace-decisiones` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/014-plugin-marketplace-decisiones/spec.md` (issue #14)

## Summary

- **Plugin**: sin cambios en sus piezas; se completa `plugins/andino-guardrails/README.md`
  (instalación por comandos, requisitos, advertencia de `exigir_spec`, cómo deshabilitar) y
  se verifica la instalación en un repositorio vacío desde GitHub.
- **`DECISIONES.md`** (nuevo, raíz): dos tablas, ecosistema de Claude Code y reglas de
  negocio, con la alternativa descartada y el enlace al `research.md` de origen.
- **Script de entrega** (`scripts/armar_entrega.py`, nuevo, con su test): `.zip` con los
  archivos versionados y `.git`, exclusiones defensivas, búsqueda de credenciales en el
  árbol y el historial, y límite de 50 MB.
- **Visibilidad**: verificación del repositorio y el Project sin sesión.
- **README**: sección de entrega y enlace a `DECISIONES.md`.

No cambia nada en `src/`. Decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14 (el script solo usa la biblioteca estándar, como los
hooks del plugin)

**Primary Dependencies**: `zipfile`, `subprocess` (git), `re`, `pathlib`; `git` en el PATH

**Storage**: ninguno (el `.zip` en `dist/`, ignorado por git)

**Testing**: `pytest` determinista con repositorios git temporales; verificaciones
manuales registradas para el plugin y la visibilidad

**Target Platform**: Windows y Linux/macOS

**Project Type**: herramientas y documentación del proyecto `uv`

**Performance Goals**: el script arma y verifica en menos de 1 minuto (SC-005)

**Constraints**:
- Nada de lo no versionado entra al `.zip`.
- Ningún valor con forma de credencial se muestra ni se escribe como literal en los tests.
- `DECISIONES.md` de máximo dos páginas.

**Scale/Scope**: 2 archivos nuevos en `scripts/`, `DECISIONES.md`, cambios en el README
del plugin, el README, `.gitignore` (`dist/`) y `pyproject.toml` (`testpaths`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | Sin cambios; `DECISIONES.md` documenta su nivel de garantía. | ✅ |
| II. Garantías deterministas | La verificación de la entrega es un script que falla cerrado. Lo manual (instalación del plugin, visibilidad) se registra porque depende de Claude Code y de GitHub. | ✅ |
| III. Datos ficticios y cero credenciales | El script busca credenciales en el árbol y el historial antes de entregar; los tests arman los valores de ejemplo en tiempo de ejecución. | ✅ |
| IV. Spec-first | Spec aprobada; no se escribe en `src/`. | ✅ |
| V. Contrato de herramientas | No aplica (no hay herramientas MCP nuevas). | ✅ |
| VI. Tests en dos niveles | Test determinista junto al script; sin escenarios nuevos. | ✅ |
| VII. Simplicidad y trazabilidad | Cumple la parte que faltaba: `DECISIONES.md`. Un script en Python estándar para los dos sistemas. | ✅ |

**Resultado**: todos los gates pasan. **Re-evaluación tras la fase 1**: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/014-plugin-marketplace-decisiones/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/armar-entrega.md
├── checklists/requirements.md
└── tasks.md                     # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
scripts/
├── armar_entrega.py             # nuevo
└── test_armar_entrega.py        # nuevo
DECISIONES.md                    # nuevo
plugins/andino-guardrails/README.md   # mod
README.md                        # mod: entrega y enlace a DECISIONES.md
.gitignore                       # mod: dist/
pyproject.toml                   # mod: testpaths con scripts
```

**Structure Decision**: el script vive en `scripts/` (no es parte del agente ni del
plugin) con su test al lado; `DECISIONES.md` en la raíz, como pide el issue
([research.md R3, R4](research.md)).

## Orden de implementación

1. **Script de entrega** con su test primero (R4, R5).
2. **`DECISIONES.md`** (R3).
3. **README del plugin** y **README** (R1).
4. **Instalación del plugin** en un repositorio vacío desde GitHub (R2): el plugin ya está
   en `main` desde el #3, así que se prueba antes del PR y se registra en `tasks.md`.
5. **Verificación**: `uv run pytest`, correr el script, contar palabras, visibilidad (R6).

## Riesgos

| Riesgo | Mitigación |
|---|---|
| La instalación desde GitHub falla en otro repositorio | Se prueba antes del PR sobre `main` (el plugin ya está ahí); si falla, se corrige en este ticket |
| El `.zip` se acerca a 50 MB (video en el árbol y en `.git`) | Hoy ronda 33 MB; el script avisa desde 40 MB |
| Falsos positivos en la búsqueda de credenciales | Patrones específicos con longitud mínima; los ejemplos documentados del repo no los cumplen; test con casos negativos |
| El Project es privado | El desarrollador cambia la visibilidad; se verifica sin sesión |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
