# Research: Plugin, marketplace y DECISIONES.md

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

## R1. El plugin ya cumple el empaquetado

- **Decision**: no se cambian las piezas del plugin. Ya empaqueta el subagente
  `auditor-cumplimiento` (`agents/`), la skill `revisar-cumplimiento` (`skills/`) y los
  hooks `bloquear_pii`, `exigir_spec` y `formatear` (`hooks/hooks.json`, con rutas
  `${CLAUDE_PLUGIN_ROOT}`). El marketplace `.claude-plugin/marketplace.json` lo publica con
  `source: ./plugins/andino-guardrails`. El ticket verifica la instalación desde fuera y
  completa `plugins/andino-guardrails/README.md`.
- **Rationale**: FR-001 ya se cumple desde el #3; cambiar los hooks no es parte del issue.
- **Alternatives considered**: generalizar `exigir_spec` (por ejemplo, desactivarlo si no
  hay carpeta `specs/`). Cambia una garantía del proyecto (principio IV) por comodidad de
  otro equipo; se documenta cómo deshabilitar el plugin o el hook en su lugar.

## R2. Prueba de instalación en un repositorio vacío

- **Decision**: verificación manual registrada en `tasks.md`: crear una carpeta vacía con
  `git init`, abrir Claude Code y ejecutar `/plugin marketplace add
  johnlizarazo/andino-dispute-agent` y `/plugin install andino-guardrails@banco-andino`.
  Luego comprobar: `/plugin` lo muestra habilitado; `/agents` lista
  `andino-guardrails:auditor-cumplimiento`; la skill aparece como
  `/andino-guardrails:revisar-cumplimiento`; pedirle a Claude que escriba un archivo con un
  número que pasa Luhn (generado en el momento, nunca guardado) y ver el bloqueo.
- **Rationale**: depende de Claude Code y de GitHub; no hay forma determinista de probarlo
  dentro de `pytest`. El marketplace se lee de la rama por omisión del repositorio en
  GitHub, y el plugin ya está en `main` desde el #3, así que la prueba puede hacerse antes
  del merge; los cambios de este ticket al README del plugin se ven tras el merge.
- **Alternatives considered**: probar con el marketplace local (`source: directory`), que ya
  usa este repo: no prueba lo que pide el issue (instalar desde GitHub).

## R3. `DECISIONES.md`

- **Decision**: un archivo en la raíz con dos tablas y un párrafo de criterio:
  1. **Ecosistema de Claude Code**: necesidad → mecanismo → dónde → alternativa descartada
     → origen (enlace al `research.md` del ticket). Filas: memoria del proyecto, memoria
     personal, reglas por ruta, skill de inicio de ticket, comando `/abrir-pr`, revisor
     independiente, hooks de datos, de spec-first y de formato, auditor y skill de
     cumplimiento en el plugin, permisos sobre `.env*`, servidores MCP, plugin y
     marketplace, CI, paso a *Done*.
  2. **Reglas de negocio del agente**: regla → nivel (diseño, hook o instrucción y test) →
     dónde → por qué.
  Máximo unas 900 palabras, verificado con un conteo en el quickstart.
- **Rationale**: FR-005 y FR-006; el principio VII exige que la justificación de cada pieza
  viva ahí. El contenido sale de los `research.md` (001 R1–R5, 002 R1–R8, 003 R1–R11 y los
  del agente 008–011), sin reabrir decisiones.
- **Alternatives considered**: un documento largo por ticket (supera dos páginas; ya existen
  los `research.md`); enlazar solo a los `research.md` (el evaluador tendría que recorrer
  catorce carpetas).

## R4. Script de entrega

- **Decision**: `scripts/armar_entrega.py`, solo biblioteca estándar, que se corre con
  `uv run --no-project python scripts/armar_entrega.py [--salida RUTA]` en Windows y en
  Linux/macOS:
  1. Lista los archivos versionados con `git ls-files -z` (lo no versionado no entra) y
     agrega todo el directorio `.git`.
  2. Aplica además un filtro de exclusión defensivo (`.venv/`, `.env*` salvo
     `.env.example`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `node_modules/`,
     `*.egg-info/`, `dist/`, `build/`, `.chainlit/`, `.files/`, `CLAUDE.local.md`,
     `.claude/settings.local.json`).
  3. Busca credenciales en el contenido de los archivos versionados y en todo el historial
     (`git log -p --all`): tokens de GitHub (`ghp_`, `gho_`, `github_pat_`), claves de
     Anthropic (`sk-ant-`), claves de AWS (`AKIA…`) y bloques `PRIVATE KEY`. Informa archivo
     o commit, nunca el valor. Si encuentra algo, no crea el `.zip`.
  4. Escribe el `.zip` (comprimido) en `dist/entrega-andino-dispute-agent.zip` por omisión,
     en un archivo temporal que solo se renombra si pasa las verificaciones.
  5. Falla si pesa 50 MB o más; avisa si supera 40 MB (margen del 80 %).
  Código de salida 0 si todo pasa, 1 si falla una verificación.
- **Rationale**: FR-007 a FR-011. Partir de `git ls-files` garantiza que no entren archivos
  locales; revisar el historial cubre credenciales que vivan en `.git` aunque ya no estén en
  el árbol. Python estándar corre igual en los dos sistemas (como los hooks del plugin).
- **Alternatives considered**: `git archive` (no incluye `.git`, que el issue exige); un
  script de PowerShell y otro de bash (dos implementaciones que pueden divergir); comprimir
  la carpeta entera con exclusiones (arrastra cualquier archivo local olvidado).

## R5. Tests del script

- **Decision**: `scripts/test_armar_entrega.py`, determinista: un repositorio git temporal
  (`tmp_path`, `git init`) con archivos versionados, un `.env`, un `.venv/` y cachés sin
  versionar; se comprueba el contenido del `.zip`, que el `.env.example` sí entra, que un
  token de ejemplo armado en tiempo de ejecución en un archivo o en un commit anterior hace
  fallar sin mostrar el valor y sin dejar `.zip`, y el límite de tamaño con un umbral
  inyectable. Se agrega `scripts` a `testpaths`.
- **Rationale**: principio VI (test junto al módulo, sin red); los valores con forma de
  credencial se arman en el test, nunca como literales (principio III y el hook
  `bloquear_pii`).
- **Alternatives considered**: probar solo a mano (el script es justo lo que no debe fallar).

## R6. Visibilidad en GitHub

- **Decision**: verificación sin sesión: `GET https://api.github.com/repos/johnlizarazo/andino-dispute-agent`
  sin token debe responder 200 con `"private": false`, y la página del Project
  (`https://github.com/users/johnlizarazo/projects/1`) debe abrir en una ventana privada del
  navegador. Si el Project es privado, el desarrollador lo cambia a público en su
  configuración (Settings del Project → Visibility). Se registra en `tasks.md`.
- **Rationale**: FR-012; la visibilidad es una configuración, no código.
- **Alternatives considered**: invitar a los evaluadores (exige conocerlos de antemano).
