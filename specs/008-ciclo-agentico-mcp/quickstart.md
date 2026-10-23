# Quickstart: Ciclo agéntico y conexión al MCP (issue #8)

## Prerrequisitos

- `uv sync` hecho.
- `ANTHROPIC_API_KEY` definida en el entorno del desarrollador (no se escribe aquí ni en
  ningún archivo del repositorio). Para comprobar solo que existe, sin ver el valor:

En PowerShell:

```powershell
Test-Path Env:ANTHROPIC_API_KEY
```

En Bash:

```bash
test -n "$ANTHROPIC_API_KEY" && echo definida || echo falta
```

- En Linux o macOS, sobre un clon limpio: `uv python install 3.14` si hace falta y luego
  `uv sync` (no se copia `.venv`, que es propio de cada sistema).

## 1. Tests deterministas

```bash
uv run pytest
```

Esperado: todo en verde, sin llamar a la API.

## 2. Escenario de punta a punta

```bash
uv run pytest -m e2e
```

Esperado: el escenario de falla transitoria pasa (se salta si falta la credencial).

## 3. Conversación en la terminal

```bash
uv run --no-sync python -m agente_disputas
```

| Paso | Qué escribir | Esperado |
|---|---|---|
| 1 | un saludo y "no reconozco unos cobros" | el agente pide identificarse (documento, nombre o últimos 4) |
| 2 | el documento `CC-FIC-0001` | el agente busca, encuentra un cliente y pide el dato de verificación |
| 3 | una línea vacía | nada se envía; la terminal sigue esperando |
| 4 | `/salir` | despedida y fin sin traza |

Variante: sin `ANTHROPIC_API_KEY` en la sesión, el comando termina con un mensaje que nombra la
variable, sin traza. Con la configuración de fallas inválida, termina diciendo que el core no
arrancó:

En Bash:

```bash
CORE_BANCARIO_FALLAS="op:0" uv run --no-sync python -m agente_disputas
```

En PowerShell:

```powershell
$env:CORE_BANCARIO_FALLAS = "op:0"; uv run --no-sync python -m agente_disputas; Remove-Item Env:CORE_BANCARIO_FALLAS
```

## 3b. En Linux (cuando haya una máquina o contenedor disponible)

Sobre un clon limpio con `uv sync` y `ANTHROPIC_API_KEY` exportada: repetir §1, §2 y los pasos
1 y 4 de la tabla de §3. Esperado: el mismo resultado que en Windows. Los tests deterministas
ya corren en Linux en cada PR (CI `guardrails` en `ubuntu-latest`); esta verificación cubre el
CLI empaquetado del SDK para Linux y la conversación real.

## 4. Escaneo de datos

`bloquear_pii.py --diff` sobre el diff de la rama contra `main`: sin hallazgos.
