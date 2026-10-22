# Contrato: `.mcp.json`

Servidores MCP del proyecto. En este ticket solo GitHub; `core-bancario` se agrega en el
issue #4. Fundamento en [research.md R5](../research.md).

## Forma esperada

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer ${GITHUB_PAT}",
        "X-MCP-Toolsets": "context,repos,issues,pull_requests,projects"
      }
    }
  }
}
```

## Reglas del contrato

- `type` es obligatorio: un `url` sin `type` se interpreta como servidor stdio.
- El token solo aparece como `${GITHUB_PAT}`. No se usa `${GITHUB_PAT:-...}`: un valor por
  defecto ocultaría la falta del token.
- `X-MCP-Toolsets` incluye `projects`, que GitHub no habilita por defecto. Los nombres
  desconocidos se ignoran en silencio; por eso la verificación exige una escritura real.

## Requisitos del token (documentados en el README)

- PAT clásico con scopes `repo` y `project`.
- Guardado como variable de entorno de usuario `GITHUB_PAT`.
- Para que la sesión lo vea, hay que reiniciar la aplicación por completo.
