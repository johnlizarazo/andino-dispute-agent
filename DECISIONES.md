# Decisiones

Criterio (constitución, principio II): lo que no puede fallar se hace cumplir con
mecanismos deterministas (hooks, permisos, diseño de herramientas); lo que exige juicio va
en un subagente aislado; lo que es contexto va en memoria o reglas. Cada pieza resuelve una
necesidad concreta; el razonamiento completo está en el `research.md` del ticket enlazado.

## Ecosistema de Claude Code

| Necesidad | Mecanismo | Dónde | Alternativa descartada | Origen |
|---|---|---|---|---|
| Principios del proyecto siempre presentes | Memoria del proyecto que importa la constitución | `CLAUDE.md` → `.specify/memory/constitution.md` | Copiar los principios en `CLAUDE.md`: dos fuentes de verdad | [Constitución, *Governance*](.specify/memory/constitution.md) |
| Preferencias personales sin versionar | Memoria y settings locales | `CLAUDE.local.md`, `.claude/settings.local.json` (en `.gitignore`) | Ignorar `.claude/` entero: se perdería la configuración compartida | [001 R3](specs/001-bootstrap-proceso/research.md) |
| Secretos fuera del alcance de Claude Code | `permissions.deny` de lectura, edición y comandos sobre `.env*` | `.claude/settings.json` | Solo `.gitignore`: no impide leer el archivo | [001 R1–R2](specs/001-bootstrap-proceso/research.md) |
| Leer y mover issues y el Project | Servidor MCP `github` por HTTP con `${GITHUB_PAT}` | `.mcp.json` | Token en el archivo o en `.env` | [001 R5](specs/001-bootstrap-proceso/research.md) |
| Iniciar un ticket con argumento y dejar la spec a la vista | Skill `siguiente-ticket` con `allowed-tools` acotado | `.claude/skills/siguiente-ticket/` | `context: fork`: la spec no quedaría en la conversación para el control 1 | [002 R1–R2](specs/002-automatizacion-ciclo/research.md) |
| Revisión independiente del diff | Subagente `revisor-codigo`, solo lectura, `permissionMode: dontAsk` | `.claude/agents/revisor-codigo.md` | Revisar en la misma sesión: no es independiente | [002 R3](specs/002-automatizacion-ciclo/research.md) |
| Abrir el PR como decisión del desarrollador | Comando `/abrir-pr` con `disable-model-invocation` | `.claude/commands/abrir-pr.md` | Un hook: reacciona a eventos, no a decisiones | [002 R1](specs/002-automatizacion-ciclo/research.md) |
| Issue a *Done* al fusionar | Regla integrada "Item closed" del Project | GitHub | Una GitHub Action con token: más piezas y un secreto | [002 R8](specs/002-automatizacion-ciclo/research.md) |
| No escribir datos con forma real | Hook `PreToolUse` `bloquear_pii` (falla cerrado) | Plugin `andino-guardrails` | Instrucciones en `CLAUDE.md`: no son deterministas | [003 R1, R5](specs/003-guardrails-desarrollo/research.md) |
| Spec-first | Hook `PreToolUse` `exigir_spec` | Plugin | Leer `.specify/feature.json`: está ignorado y puede quedar viejo | [003 R7](specs/003-guardrails-desarrollo/research.md) |
| Formato consistente | Hook `PostToolUse` `formatear` (ruff) | Plugin | Formatear solo en CI: la corrección llega tarde | [003 R8](specs/003-guardrails-desarrollo/research.md) |
| Auditar la constitución antes del PR | Subagente `auditor-cumplimiento` + skill `revisar-cumplimiento` | Plugin | Dejarlo en `.claude/agents/` con `dontAsk`: más fuerte, pero no reutilizable (los agentes de plugin ignoran `permissionMode`) | [003 R9–R11](specs/003-guardrails-desarrollo/research.md) |
| Convenciones solo donde aplican | Reglas con `paths` | `.claude/rules/` | Una skill: se carga por relevancia, no por ruta; los plugins no tienen `rules/` | [003 R2](specs/003-guardrails-desarrollo/research.md) |
| Que otro equipo reutilice los guardrails | Plugin y marketplace `banco-andino`; el repo los consume | `plugins/`, `.claude-plugin/marketplace.json` | Copiar archivos entre repositorios | [003 R3](specs/003-guardrails-desarrollo/research.md) |
| Cubrir commits hechos fuera de Claude Code | Workflow con el mismo script de datos y `uv run pytest` | `.github/workflows/guardrails.yml` | Pre-commit local: depende de que cada uno lo instale | [003 R6](specs/003-guardrails-desarrollo/research.md) |
| Entrega sin archivos locales ni credenciales | Script con `git ls-files` + `.git`, búsqueda en árbol e historial | `scripts/armar_entrega.py` | `git archive`: no incluye `.git` | [014 R4](specs/014-plugin-marketplace-decisiones/research.md) |

## Reglas de negocio del agente

| Regla | Nivel | Dónde | Por qué |
|---|---|---|---|
| 1. Identidad verificada | Hook | `PostToolUse` registra al verificado; `PreToolUse` niega sin identidad o con producto ajeno (`controles.py`) | Un prompt puede omitirse; el hook no ([009](specs/009-hooks-sdk-r1-r2/research.md)) |
| 2. Umbral de $500.000 | Hook | `PreToolUse` lee el monto del core por `transaccion_id`, nunca del modelo | El monto del modelo no es confiable ([009 R5](specs/009-hooks-sdk-r1-r2/research.md)) |
| Escalar tras negación | Hook `Stop` con tope de 2 | `antes_de_terminar` sobre los pendientes | El turno no puede cerrar con un escalamiento pendiente ([010](specs/010-escalamiento-criterio-solicitudes/research.md)) |
| 3. Bloqueo inmediato | Imposible por diseño | `bloquear_tarjeta` no tiene aprobación intermedia | No hay forma de esperar un analista |
| 4. Persona a pedido | Instrucción + test de escenario | Prompt con ejemplos positivos y negativos; `test_caso_2_persona` | Exige interpretar; palabras clave fallarían con "alguien usó mi tarjeta" ([010 R6](specs/010-escalamiento-criterio-solicitudes/research.md)) |
| 5. Fuera de política | Diseño + hook | El core rechaza con `FUERA_DE_POLITICA` (no reintentable) y el `Stop` obliga a escalar | El servidor decide la política, no el modelo |
| Delegación al subagente | Hook + diseño | `antes_de_delegar` exige cliente verificado y `<contexto>` completo; el subagente solo puede consultar | Delegar no abre una vía para saltarse las reglas ([011](specs/011-subagente-analista-transacciones/research.md)) |
