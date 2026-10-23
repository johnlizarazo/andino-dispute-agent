# Contrato: workflow de GitHub

Fundamento en [research.md R6](../research.md). Archivo: `.github/workflows/guardrails.yml`.

```yaml
name: guardrails
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  guardrails:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0
      - uses: astral-sh/setup-uv@v6
      - name: Datos con forma real en el diff
        run: |
          BASE="${{ github.event.pull_request.base.sha || github.event.before }}"
          if [ -z "$BASE" ] || [ "$BASE" = "0000000000000000000000000000000000000000" ]; then
            BASE="$(git rev-parse HEAD~1)"
          fi
          git diff --unified=0 "$BASE"...HEAD > cambios.diff
          uv run --no-project python plugins/andino-guardrails/hooks/bloquear_pii.py --diff cambios.diff
      - name: Tests deterministas
        run: uv run pytest
```

## Reglas

- **Sin secretos:** `permissions: contents: read`.
- **Mismo script que el hook:** una sola regla de detección para todo el proyecto.
- **El job falla** si hay hallazgos o si fallan los tests.
- **Versiones de las actions:** se fijan en la implementación con las versiones vigentes:
  `actions/checkout@v7` y `astral-sh/setup-uv@v10.3.2`. setup-uv no publica etiqueta mayor
  (`v10` no existe), y la primera ejecución del job falló por eso. Ahora se comprueba que
  cada etiqueta exista con `gh api repos/<action>/git/ref/tags/<etiqueta>`.
