# Contrato: script de entrega

**Feature**: [../spec.md](../spec.md) · **Modelo**: [../data-model.md](../data-model.md)

## Uso

```bash
uv run --no-project python scripts/armar_entrega.py [--salida RUTA]
```

- Se corre desde la raíz del repositorio (falla con un mensaje claro si no hay `.git`).
- Por omisión escribe `dist/entrega-andino-dispute-agent.zip` (`dist/` está en `.gitignore`).

## Salida

| Situación | Código | Mensaje |
|---|---|---|
| Todo pasa | 0 | Ruta, tamaño en MB y cantidad de archivos |
| Pasa con más de 40 MB | 0 | Lo anterior y un aviso de que se acerca al límite |
| 50 MB o más | 1 | Tamaño y límite; no deja el `.zip` |
| Credenciales encontradas | 1 | Una línea por hallazgo: tipo y archivo o commit, sin el valor; no crea el `.zip` |
| No es un repositorio git | 1 | Mensaje claro |

## Contenido del `.zip`

- Todos los archivos que lista `git ls-files` y el directorio `.git` completo, con sus rutas
  relativas a la raíz.
- Nunca: las exclusiones del [modelo](../data-model.md), aunque estuvieran versionadas.
