# Evidencias de las pruebas automáticas

Salida de la ejecución de las pruebas del backend con pytest sobre PostgreSQL 16 (18 de noviembre de 2026).

| Archivo | Comando | Resultado |
|---|---|---|
| [`pytest-suite-completa.txt`](pytest-suite-completa.txt) | `pytest -q` | 232 pruebas aprobadas |
| [`pytest-maquina-de-estados.txt`](pytest-maquina-de-estados.txt) | `pytest -v tests/test_maquina_estados_inscripcion.py` | 26 aprobadas (casos CP-01 a CP-25) |
| [`pytest-flujos-alternativos.txt`](pytest-flujos-alternativos.txt) | `pytest -q tests/test_alt_*.py` | 99 aprobadas |

## Cómo repetirlas

```bash
cd Backend-plataforma-de-cursos-online
pip install -r requirements-dev.txt
pytest
```

Por defecto las pruebas usan una base SQLite temporal, así que no necesitan PostgreSQL ni tocan los datos reales. Para ejecutarlas sobre PostgreSQL se define la variable `PRUEBAS_DATABASE_URL` con la cadena de conexión de una base vacía.

## Qué cubren

| Archivos | Qué verifican | Pruebas |
|---|---|---|
| `test_seguridad_usuarios.py`, `test_reglas_hu.py`, `test_pagos.py`, `test_factory_preguntas.py`, `test_presentacion_evaluacion.py`, `test_cierre_y_certificado.py`, `test_aula.py`, `test_historial.py` | Flujos principales, reglas de las historias y los cinco patrones GoF (Entregable 2) | 107 |
| `test_maquina_estados_inscripcion.py` | Transiciones de la máquina de estados de la inscripción | 26 |
| `test_alt_*.py` (siete archivos, uno por tema) | Flujos alternativos, validaciones y errores controlados | 99 |
