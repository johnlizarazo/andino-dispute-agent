# Quickstart: Plugin, marketplace y DECISIONES.md

**Feature**: [spec.md](spec.md) · **Contrato**: [contracts/armar-entrega.md](contracts/armar-entrega.md)

## 1. Tests deterministas

```bash
uv run pytest
```

Esperado: todo en verde, incluido `scripts/test_armar_entrega.py`.

## 2. Armar la entrega

```bash
uv run --no-project python scripts/armar_entrega.py
```

Esperado: código 0, `dist/entrega-andino-dispute-agent.zip` de menos de 50 MB, sin
hallazgos. Abrir el `.zip` y comprobar que tiene `.git/` y no tiene `.venv/`, `.env` ni
cachés. Repetir en Linux o macOS si hay una máquina disponible.

## 3. DECISIONES.md

Comprobar que cada pieza del ecosistema aparece con su alternativa descartada y medir el
largo (máximo unas 900 palabras):

```bash
uv run --no-project python -c "print(len(open('DECISIONES.md', encoding='utf-8').read().split()))"
```

## 4. Instalación del plugin en un repositorio vacío

El marketplace se lee desde `main` en GitHub, donde el plugin ya está desde el #3. En una
carpeta nueva, fuera de este repositorio:

```bash
git init prueba-plugin
```

Abrir Claude Code en esa carpeta y ejecutar `/plugin marketplace add
johnlizarazo/andino-dispute-agent` y `/plugin install andino-guardrails@banco-andino`.
Comprobar en `/plugin` que está habilitado, en `/agents` el auditor y que la skill
`/andino-guardrails:revisar-cumplimiento` existe; pedir a Claude que escriba un archivo con
un número de tarjeta con forma real y ver el bloqueo.

## 5. Visibilidad

```bash
curl -s https://api.github.com/repos/johnlizarazo/andino-dispute-agent
```

Esperado: `"private": false`. Abrir el Project en una ventana privada del navegador.
