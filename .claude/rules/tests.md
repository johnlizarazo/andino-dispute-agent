---
paths:
  - "src/**/test_*.py"
  - "tests/**/*.py"
  - "plugins/**/test_*.py"
---

# Convención de tests

- El test vive en la misma carpeta que el módulo que prueba y se llama `test_<módulo>.py`.
- Nombres de test en español y descriptivos: `test_<comportamiento_esperado>`.
- Los tests deterministas no usan red, API ni reloj real. Las fechas relativas ("ayer") se
  calculan respecto de un "hoy" inyectado.
- Los escenarios que llaman al modelo van en `tests/escenarios/`, marcados
  `@pytest.mark.e2e`. Sus mensajes difieren de los ejemplos del prompt de sistema.
- Solo datos ficticios. Los números que deban pasar Luhn y los documentos de prueba se
  generan en el test; nunca como literales.
