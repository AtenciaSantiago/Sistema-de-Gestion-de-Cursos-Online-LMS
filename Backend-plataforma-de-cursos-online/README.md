# Backend · Campus Digital (API REST)

API del Sistema de Gestión de Cursos Online, hecha con **FastAPI + SQLAlchemy + PostgreSQL**.
Las instrucciones completas, los usuarios de demostración y la tabla de historias de usuario
están en el [README principal](../README.md).

## Cómo correrla

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python migrardb.py               # crea o actualiza las tablas
python datos_demo.py             # (opcional, base vacía) datos de demostración
python main.py                   # o: uvicorn src.app:app --reload
```

Archivo `.env` necesario:

```
DATABASE_URL=postgresql://usuario:clave@servidor/basedatos
SECRET_KEY=una-clave-larga-y-secreta
ALGORITHM=HS256
```

Documentación interactiva de todos los endpoints: http://127.0.0.1:8000/docs

## Cómo está organizada

| Carpeta | Qué tiene |
|---|---|
| `src/entities/` | Las tablas de la base de datos (SQLAlchemy) |
| `src/schemas/` | Lo que entra y sale de la API (Pydantic) |
| `src/services/` | Las reglas de negocio de cada historia de usuario |
| `src/endpoints/` | Las rutas de la API y los permisos por rol |
| `src/patrones/` | Los 5 patrones GoF: Factory Method, Strategy, Adapter, Observer y Template Method |
| `tests/` | Pruebas automáticas (pytest) |

## Permisos por rol (RN-02)

- **Admin**: usuarios, publicar u ocultar cursos, asignar profesor, matrícula manual y cancelación, auditoría de pagos y de cierres.
- **Docente**: solo los cursos que tiene asignados (lecciones, materiales, evaluaciones, preguntas y sus estudiantes).
- **Estudiante**: catálogo, pago, aula virtual, evaluaciones y certificado.
- Las notas, los pagos y los certificados los genera el sistema; nadie los escribe a mano.

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest
```

Por defecto usan una base SQLite temporal. Para probar contra PostgreSQL:
`PRUEBAS_DATABASE_URL=postgresql://usuario@localhost:5432/lms_pruebas pytest`

## Institución

Instituto Tecnológico Metropolitano (ITM) · Diseño de Sistemas de Información
