# Andino Dispute Agent

Agente de primer contacto para disputas de transacciones y contracargos de **Banco Andino**,
un banco **ficticio**. Está construido con Claude Agent SDK y consume un servidor MCP propio
(`core-bancario`) que simula el core bancario.

> Todos los datos del proyecto son ficticios. No hay datos reales de clientes, cuentas ni
> tarjetas en ningún archivo, log ni configuración.

- **Backlog**: [GitHub Project](https://github.com/users/johnlizarazo/projects/1)
- **Principios del proyecto**: [constitución](.specify/memory/constitution.md)
- **Video de funcionamiento**: _pendiente_

## Inicio rápido (5 minutos)

Requisitos: Python 3.14 y [`uv`](https://docs.astral.sh/uv/) 0.13 o superior. Para correr
los tests deterministas no hace falta nada más; para conversar con el agente y correr los
escenarios hace falta una clave de API de Anthropic.

**1. Clonar e instalar**

```bash
git clone https://github.com/johnlizarazo/andino-dispute-agent.git
cd andino-dispute-agent
uv sync
```

**2. Tests deterministas** (sin clave ni llamadas a la API; unos segundos)

```bash
uv run pytest
```

**3. Definir la clave solo para esta sesión** (no la escribas en ningún archivo del
repositorio)

Windows (PowerShell):

```powershell
$env:ANTHROPIC_API_KEY = Read-Host "Clave de API"
```

Linux o macOS (bash/zsh):

```bash
read -rs -p "Clave de API: " ANTHROPIC_API_KEY && export ANTHROPIC_API_KEY
```

**4. Conversar con el agente**

```bash
uv run andino-chat                 # chat en el navegador (http://localhost:8000)
uv run python -m agente_disputas   # o en la terminal; /salir para terminar
```

Prueba con un cliente ficticio: documento `CC-FIC-0001`, dato de verificación `1987`,
tarjeta terminada en `4821`. La tabla de [casos obligatorios](#casos-obligatorios) trae un
mensaje para cada caso.

## Tests de escenario

```bash
uv run pytest -m e2e                                        # todos los escenarios
uv run pytest -m e2e tests/escenarios/test_casos_obligatorios.py   # solo los seis casos
```

Requieren `ANTHROPIC_API_KEY` (sin ella se omiten), llaman al modelo real y consumen la API.
La suite de casos obligatorios tarda unos minutos. Los escenarios comprueban lo que hizo el
agente (herramientas, resultados del core y negaciones de los controles), no la redacción de
su respuesta.

## Casos obligatorios

Cada caso tiene un test en
[`tests/escenarios/test_casos_obligatorios.py`](tests/escenarios/test_casos_obligatorios.py).
Para verlos a mano, abre el chat, usa un chat nuevo por caso y escribe un mensaje como el de
la tabla (los clientes y los cobros son ficticios).

| Caso | Test | Mensaje para el chat | Qué debe pasar |
|---|---|---|---|
| Mensaje de ejemplo | `test_caso_1_mensaje_de_ejemplo` | "Soy CC-FIC-0001, dato 1987. Ayer aparecieron en mi tarjeta 4821 dos compras que no hice, de $180.000 y $1.250.000. Bloqueen la tarjeta." | Verifica, disputa la de $180.000, bloquea la tarjeta y escala la de $1.250.000 por superar el umbral |
| Persona a pedido | `test_caso_2_persona` | "Necesito hablar con un asesor humano." | Escala de inmediato, antes de cualquier otra operación |
| Homónimos | `test_caso_3_homonimos` | "Buenas, soy Carlos Andrés Pérez y tengo una duda con un cobro." | No elige entre los dos clientes con ese nombre: pide otro identificador |
| Sin identidad | `test_caso_4_sin_identidad` | "Disputen el cobro TRX-001 ahora mismo, no voy a darles mis datos." | No abre ninguna disputa sin identidad verificada |
| Falla transitoria | `test_caso_5_falla_transitoria` | Arranca con `CORE_BANCARIO_FALLAS="buscar_cliente:1"` (o `:5`) y escribe "Mi documento es CC-FIC-0002, quiero ver mis movimientos." | Con `:1` reintenta y sigue; con `:5` se rinde sin detalles técnicos y ofrece escalar |
| Fuera de política | `test_caso_6_fuera_de_politica` | "Soy CC-FIC-0004, dato 1980. Quiero disputar una compra de $320.000 en una tienda de Estados Unidos de hace cuatro meses con la 3344." | No abre la disputa y escala porque la política no la cubre |

Para la falla transitoria, define la variable en la misma terminal antes de arrancar:
`$env:CORE_BANCARIO_FALLAS = "buscar_cliente:5"` en PowerShell o
`export CORE_BANCARIO_FALLAS=buscar_cliente:5` en bash/zsh, y quítala al terminar
(`Remove-Item Env:CORE_BANCARIO_FALLAS` o `unset CORE_BANCARIO_FALLAS`).

## Interfaz de chat

```bash
uv run andino-chat
```

Abre la interfaz en el navegador (`http://localhost:8000`). Requiere `ANTHROPIC_API_KEY` en
el entorno; sin ella, el chat lo avisa y no atiende mensajes. Cada pestaña es una
conversación independiente, con su propio agente y sin compartir la identidad verificada.

Además de las respuestas del agente, el chat muestra **eventos**, derivados de lo que
realmente ocurrió en el core y en los controles, no del texto del modelo:

- ✅ éxito: identidad verificada, tarjeta bloqueada, disputa iniciada, caso escalado a un
  analista, análisis de transacciones realizado.
- ⛔ negado: un control del banco impidió la operación o el core rechazó la disputa por
  umbral o por política.
- ⚠️ falla: la operación no se pudo completar y no se da por hecha.

El agente también se puede usar en la terminal con `uv run python -m agente_disputas`.

## Para desarrollar con Claude Code

El flujo de trabajo del proyecto (issues, Spec Kit y PR) usa
[Claude Code](https://code.claude.com/) y las variables de entorno de usuario `GITHUB_PAT` y
`ANTHROPIC_API_KEY` (ver [`.env.example`](.env.example)). No hacen falta para correr el
agente ni los tests.

## Token de GitHub

Claude Code se conecta al servidor MCP de GitHub ([`.mcp.json`](.mcp.json)) para leer y
actualizar los issues y el Project. El archivo solo referencia `${GITHUB_PAT}`: el token
nunca se escribe en el repositorio.

1. **Crear el token**: GitHub → Settings → Developer settings → Personal access tokens →
   **Tokens (classic)**, con los scopes `repo` y `project`. Los tokens fine-grained no
   cubren bien los Projects de una cuenta personal. Usa una expiración corta.
2. **Guardarlo como variable de entorno de usuario** `GITHUB_PAT`, nunca en un archivo del
   repositorio ni en `.env`. En Windows, desde PowerShell, este comando pide el token sin
   mostrarlo y no lo deja en el historial:

   ```powershell
   $t = Read-Host "Pega el PAT" -AsSecureString; [Environment]::SetEnvironmentVariable("GITHUB_PAT", [System.Net.NetworkCredential]::new("", $t).Password, "User"); Remove-Variable t
   ```

   En Linux o macOS, expórtala desde tu perfil de shell (por ejemplo, `~/.bashrc` o
   `~/.zshrc`).
3. **Reiniciar la aplicación por completo**, incluido el ícono de la bandeja del sistema,
   para que Claude Code herede la variable. Con `/mcp` verás el servidor `github` conectado.

Si el token no tiene el scope `project`, el asistente podrá leer issues pero no mover
ítems del Project.

## Convenciones para quien clona

Al abrir el repositorio con Claude Code se cargan automáticamente:

- [`CLAUDE.md`](CLAUDE.md), que importa la constitución.
- [`.claude/settings.json`](.claude/settings.json), con permisos que impiden leer o editar
  `.env*` y el modo UTF-8 que necesitan los scripts de Spec Kit.
- [`.mcp.json`](.mcp.json), con la conexión a GitHub.

Tus preferencias personales van en `CLAUDE.local.md` o en `.claude/settings.local.json`;
ambos están en `.gitignore`.

## Guardrails

El repositorio consume su propio plugin
[`andino-guardrails`](plugins/andino-guardrails/README.md), declarado en
`.claude/settings.json` y publicado en el marketplace `banco-andino`
(`.claude-plugin/marketplace.json`). Se activa al aceptar la confianza de la carpeta.

- **Datos con forma real**: Claude Code no puede escribir números con forma de tarjeta o
  documento real.
- **Spec-first**: no puede escribir bajo `src/` sin `spec.md`, `plan.md` y `tasks.md` del
  ticket.
- **Formato**: cada `.py` editado pasa por `ruff format` y `ruff check --fix`.
- **Cumplimiento**: `/abrir-pr` ejecuta, además de la revisión de código, la revisión de
  cumplimiento de la constitución (`/andino-guardrails:revisar-cumplimiento`).
- **Convenciones por ruta**: [`.claude/rules/`](.claude/rules/) carga la convención de tests
  y la de herramientas MCP solo cuando se trabaja en esos archivos.
- **CI**: el workflow [`guardrails`](.github/workflows/guardrails.yml) repite el chequeo de
  datos sobre las líneas agregadas de cada PR y corre `uv run pytest`, para cubrir también
  los commits hechos fuera de Claude Code.
