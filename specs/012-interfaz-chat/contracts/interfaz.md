# Contrato: interfaz de chat

**Feature**: [../spec.md](../spec.md)

## Arranque

```bash
uv run andino-chat
```

- Requiere `ANTHROPIC_API_KEY` en el entorno (Chainlit también lee un `.env` local del
  desarrollador; el repositorio no lo trae). Opcionales: `ANDINO_MODELO`,
  `CORE_BANCARIO_FALLAS`, igual que la línea de comandos.
- Abre la interfaz en el navegador (puerto por omisión de Chainlit, 8000).

## Ciclo de una conversación

| Momento | Comportamiento |
|---|---|
| Inicio del chat | Crea una `SesionChat` (el servidor arranca aunque falte la credencial; la comprobación es por conversación). Sin credencial → aviso de credencial faltante y no se atienden mensajes. Core no conectado → "El core bancario no arrancó; …" y no se atienden mensajes. Si no, `BIENVENIDA_WEB`. |
| Mensaje del cliente | Se procesa el turno; los eventos se muestran a medida que ocurren (autor `Evento`); al final, la respuesta del agente (autor `Agente`) o el aviso del estado del turno. |
| Escalamiento pendiente | Tras la respuesta, `AVISO_ESCALAMIENTO_PENDIENTE` (lo emite la interfaz). |
| Sesión perdida | `AVISO_SESION`; la conversación no acepta más mensajes. |
| Fin del chat | Se cierra la sesión y se libera el cliente del agente. |

## Formato de un evento

`<prefijo> **<título>**` en una línea y, si hay, `<detalle>` debajo. Prefijos: ✅ exito,
⛔ negado, ⚠️ falla. Ejemplo: `✅ **Tarjeta bloqueada**` / `•••• 4821`. El título va en
negrita porque Chainlit 2 no muestra el nombre del autor junto al mensaje (verificación
T011).

## Lo que la interfaz no hace

- No cambia el agente, el prompt, los controles ni el core (FR-003).
- No muestra trazas, códigos crudos, nombres de herramientas ni el razonamiento del modelo.
- No guarda historial entre reinicios ni autentica usuarios.
