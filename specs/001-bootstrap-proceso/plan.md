# Implementation Plan: Bootstrap del proceso

**Branch**: `001-bootstrap-proceso` | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-bootstrap-proceso/spec.md` (issue #1)

## Summary

Dejar el repositorio listo para el resto del proyecto. Cuatro frentes:

1. **Proteger los secretos:** exclusiones de git, más permisos compartidos de Claude Code que
   niegan leer y editar `.env*` por herramientas de archivos y por consola.
2. **Entregar las convenciones al clonar:** `CLAUDE.md` que importa la constitución, settings
   compartidos con `PYTHONUTF8=1` para Spec Kit, y lo personal ignorado.
3. **Conectar el asistente al Project de GitHub:** `.mcp.json` sin credenciales, verificado
   con una escritura real.
4. **Fijar la estructura base:** dos paquetes vacíos, configuración de pytest y finales de
   línea.

Todas las decisiones técnicas están respaldadas en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14 (`requires-python = ">=3.14"`), gestionado con `uv` 0.13.2

**Primary Dependencies**:
- Ya declaradas: `claude-agent-sdk`, `mcp[cli]`, `chainlit`; en desarrollo `pytest`,
  `pytest-asyncio`, `ruff`.
- Este ticket no agrega dependencias.

**Storage**: N/A

**Testing**: `pytest`; tests de humo de importación junto a cada paquete

**Target Platform**: estaciones de desarrollo Windows, Linux y macOS con Claude Code

**Project Type**: configuración del repositorio (entorno de desarrollo) más esqueleto de dos
paquetes Python

**Performance Goals**: instalación desde cero en menos de 2 minutos (SC-005)

**Constraints**:
- Ninguna credencial versionada; repositorio público.
- Cero pasos de configuración al clonar, salvo definir variables de entorno.
- Multiplataforma.

**Scale/Scope**: unos 10 archivos de configuración y 4 archivos de código (2 `__init__.py` y
2 tests de humo)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | No toca lógica de negocio. La constitución que las contiene queda versionada (FR-009). | ✅ N/A |
| II. Garantías deterministas | La protección de secretos usa permisos declarativos (deterministas), no instrucciones. La capa de consola se declara de mejor esfuerzo y la garantía fuerte es `.gitignore`. | ✅ |
| III. Datos ficticios y cero credenciales | `.env*` ignorado y negado; `.env.example` sin valores; `.mcp.json` solo con `${GITHUB_PAT}`; el token vive en el entorno del usuario. | ✅ |
| IV. Spec-first | El ticket tiene spec; este plan y `tasks.md` completan el trío antes de escribir en `src/`. La spec enlaza el issue #1 y el PR lo cerrará. | ✅ |
| V. Contrato de herramientas | Sin herramientas MCP propias en este ticket. | ✅ N/A |
| VI. Tests junto al código | Tests de humo junto a cada paquete; `uv run pytest` en verde; marcador `e2e` registrado y excluido por defecto. | ✅ |
| VII. Simplicidad y trazabilidad | Solo piezas exigidas por la spec. Cada decisión, con su alternativa descartada, queda en `research.md` como insumo de `DECISIONES.md`. La verificación del MCP queda como comentario en el issue. | ✅ |

**Resultado**: todos los gates pasan; no hay violaciones que justificar.

**Re-evaluación tras el diseño (fase 1)**: sin cambios. El diseño no agregó piezas fuera de
la spec. Los contratos (configuración) y el quickstart solo concretan lo ya evaluado.

## Project Structure

### Documentation (this feature)

```text
specs/001-bootstrap-proceso/
├── spec.md              # Especificación (aprobada)
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones y alternativas
├── data-model.md        # Fase 1: entidades de configuración
├── quickstart.md        # Fase 1: guía de validación
├── contracts/           # Fase 1: contratos de los archivos de configuración
│   ├── claude-settings.md
│   ├── mcp-json.md
│   └── gitignore.md
├── checklists/
│   └── requirements.md  # Validación de calidad de la spec
└── tasks.md             # Fase 2 (/speckit-tasks; no lo crea este comando)
```

### Source Code (repository root)

```text
.
├── CLAUDE.md                    # nuevo: instrucciones del proyecto, @import de la constitución
├── README.md                    # actualizado: propósito, requisitos, token de GitHub
├── .gitignore                   # ampliado: .env*, CLAUDE.local.md, settings.local.json
├── .gitattributes               # nuevo: LF en el repo, CRLF para .ps1
├── .env.example                 # nuevo: nombres de variables sin valores
├── .mcp.json                    # nuevo: servidor MCP de GitHub
├── .claude/
│   ├── settings.json            # nuevo: permissions.deny y env
│   └── skills/speckit-*/        # existente (Spec Kit)
├── .specify/                    # existente (Spec Kit y constitución)
├── pyproject.toml               # actualizado: descripción, módulos, pytest
├── uv.lock                      # regenerado por uv
└── src/
    ├── agente_disputas/
    │   ├── __init__.py          # nuevo, vacío salvo docstring
    │   └── test_paquete.py      # nuevo: test de humo de importación
    └── core_bancario_mcp/
        ├── __init__.py          # nuevo, vacío salvo docstring
        └── test_paquete.py      # nuevo: test de humo de importación
```

Se elimina `src/andino_dispute_agent/`.

**Structure Decision**: un solo proyecto `uv` con dos módulos bajo `src/` ([research.md R6](research.md#r6-dos-paquetes-con-uv_build)).
Los tests unitarios viven junto al código (`test_*.py` en la misma carpeta). La carpeta
`tests/` raíz queda reservada para los escenarios `e2e` del issue #13, y no se crea en este
ticket.

## Orden de implementación

1. **Protección de secretos primero** (P1): `.gitignore`, `.claude/settings.json` (deny) y
   `.env.example`.
2. **Convenciones** (P2): `env.PYTHONUTF8` en settings, `CLAUDE.md` y `.gitattributes`
   (renormalizando los archivos existentes).
3. **Estructura** (P4): paquetes, `pyproject.toml`, tests de humo y `uv sync` en limpio.
4. **Conexión con GitHub** (P3): `.mcp.json` y documentación del token en `README.md`.
5. **Verificación** (P3): requiere una sesión nueva con `GITHUB_PAT` visible. Mover el
   issue #1 con el MCP y comentar el resultado. Es el único paso que depende del entorno
   del desarrollador.

P3 va después de P4 porque su verificación exige reiniciar la sesión. Así ese reinicio
ocurre una sola vez, al final.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| `GITHUB_PAT` no visible para la sesión (ya ocurrió) | Documentar en el README que hay que cerrar la app por completo. La verificación se hace al final, en una sesión nueva. |
| Nombre de conjunto de herramientas mal escrito (se ignora en silencio) | La verificación exige una escritura real en el Project, no solo listar herramientas. |
| Las reglas de consola no cubren toda variante | Declarado como mejor esfuerzo en la spec; la garantía fuerte es que nada se versiona. |
| Renormalizar finales de línea genera un diff grande | Hacerlo en un commit separado, `chore: normalizar finales de línea`. |
| `uv.lock` cambia al cambiar la build | Se regenera con `uv sync` y se versiona en el mismo commit. |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
