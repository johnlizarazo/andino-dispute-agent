"""Bloquea datos con forma de tarjeta o documento de identidad real.

Modo hook (PreToolUse): lee el evento de Claude Code por stdin y sale con 2 si el texto
nuevo contiene un dato con forma real. Cualquier error interno también sale con 2: el
control falla cerrado.

Modo CLI (CI): ``bloquear_pii.py --diff cambios.diff`` revisa solo las líneas agregadas de
un diff unificado y sale con 1 si encuentra algo.

Solo usa la biblioteca estándar, para funcionar en el repositorio de cualquier equipo.
"""

import json
import re
import sys

PATRON_TARJETA = re.compile(
    r"(?<!\d)(?:"
    r"\d{13,19}"  # contiguo
    r"|\d{4}(?:[ -]\d{4}){2,3}(?:[ -]\d{1,3})?"  # grupos de 4: 13 a 19 dígitos
    r"|\d{4}[ -]\d{6}[ -]\d{5}"  # formato 4-6-5
    r")(?!\d)"
)
PATRON_DOCUMENTO = re.compile(
    r"(?i)(?<!\w)(?:c\.?c\.?|c[eé]dula|documento|nit|pasaporte)(?!\w)"
    r"\W{0,3}(\d{1,3}(?:\.\d{3}){1,3}|\d{6,10})(?![\d.])"
)


def luhn_valido(digitos: str) -> bool:
    total = 0
    for i, c in enumerate(reversed(digitos)):
        d = int(c)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _muestra(digitos: str) -> str:
    return "•••• " + digitos[-4:]


def buscar_hallazgos(texto: str) -> list[dict]:
    """Devuelve los datos con forma real del texto, sin incluir el valor completo."""
    hallazgos = []
    for m in PATRON_TARJETA.finditer(texto):
        digitos = re.sub(r"\D", "", m.group())
        if 13 <= len(digitos) <= 19 and luhn_valido(digitos):
            linea = texto.count("\n", 0, m.start()) + 1
            hallazgos.append({"tipo": "tarjeta", "linea": linea, "muestra": _muestra(digitos)})
    for m in PATRON_DOCUMENTO.finditer(texto):
        digitos = re.sub(r"\D", "", m.group(1))
        if 6 <= len(digitos) <= 10:
            linea = texto.count("\n", 0, m.start()) + 1
            hallazgos.append({"tipo": "documento", "linea": linea, "muestra": _muestra(digitos)})
    return hallazgos


def textos_nuevos(evento: dict) -> list[str]:
    """Extrae el texto que la herramienta va a escribir, sea cual sea su esquema."""
    entrada = evento.get("tool_input") or {}
    textos = [entrada[c] for c in ("content", "new_string", "new_source") if entrada.get(c)]
    for edicion in entrada.get("edits") or []:
        if edicion.get("new_string"):
            textos.append(edicion["new_string"])
    return textos


def _mensaje(archivo: str, hallazgo: dict) -> str:
    return (
        f"Bloqueado: dato con forma real ({hallazgo['tipo']}) en {archivo}, línea "
        f"{hallazgo['linea']} del texto nuevo: {hallazgo['muestra']}. Usa datos ficticios "
        "(tarjeta: solo últimos 4 dígitos; documento: CC-FIC-NNNN)."
    )


def modo_hook() -> int:
    evento = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    archivo = (evento.get("tool_input") or {}).get("file_path", "?")
    mensajes = [
        _mensaje(archivo, h) for texto in textos_nuevos(evento) for h in buscar_hallazgos(texto)
    ]
    if mensajes:
        print("\n".join(mensajes), file=sys.stderr)
        return 2
    return 0


def modo_diff(ruta: str) -> int:
    archivo, encontrados = "?", 0
    with open(ruta, encoding="utf-8", errors="replace") as diff:
        for numero, linea in enumerate(diff, start=1):
            if linea.startswith("+++ "):
                archivo = linea[4:].strip().removeprefix("b/")
            elif linea.startswith("+"):
                for h in buscar_hallazgos(linea[1:]):
                    print(f"{archivo} (línea {numero} del diff): {h['tipo']} {h['muestra']}")
                    encontrados += 1
    if encontrados:
        print(f"{encontrados} dato(s) con forma real en las líneas agregadas.")
    return 1 if encontrados else 0


def main() -> int:
    for flujo in (sys.stdout, sys.stderr):
        flujo.reconfigure(encoding="utf-8")
    if len(sys.argv) == 3 and sys.argv[1] == "--diff":
        return modo_diff(sys.argv[2])
    try:
        return modo_hook()
    except Exception as error:  # fallo cerrado: un error nunca deja pasar la escritura
        print(f"bloquear_pii: error interno, se bloquea por seguridad: {type(error).__name__}",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
