"""
Configuración común de las pruebas (pytest).

Las pruebas usan una base de datos SQLite temporal, así no se toca la base
real de Neon. Cada prueba arranca con la base vacía.
"""

import os
import tempfile

# Variables de entorno de prueba ANTES de importar la app.
# Por defecto SQLite temporal; para probar contra PostgreSQL real:
#   PRUEBAS_DATABASE_URL=postgresql://usuario@localhost:5432/lms_pruebas pytest
_archivo_bd = os.path.join(tempfile.mkdtemp(), "pruebas.db")
os.environ["DATABASE_URL"] = os.environ.get("PRUEBAS_DATABASE_URL", f"sqlite:///{_archivo_bd}")
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-automaticas-0123456789")
os.environ.setdefault("ALGORITHM", "HS256")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.app import app  # noqa: E402
from src.database.config import Base, SessionLocal, engine  # noqa: E402
from src.entities.Curso import Curso  # noqa: E402
from src.entities.Evaluacion import Evaluacion  # noqa: E402
from src.entities.Leccion import Leccion  # noqa: E402
from src.entities.categoria import Categoria  # noqa: E402
from src.entities.inscripcion import EstadoInscripcion, Inscripcion  # noqa: E402
from src.entities.usuario import Usuario  # noqa: E402
from src.services.usuario import _hash_contrasena  # noqa: E402
from src.utils.jwt_utils import create_token  # noqa: E402


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    sesion = SessionLocal()
    try:
        yield sesion
    finally:
        sesion.close()


@pytest.fixture()
def cliente(db):
    return TestClient(app)


def token_de(usuario: Usuario) -> dict:
    """Encabezado Authorization listo para usar en las peticiones."""
    return {"Authorization": f"Bearer {create_token(str(usuario.id_usuario))}"}


def crear_usuario(db, nombre, email, documento, rol):
    u = Usuario(
        nombre_usuario=nombre,
        tipo_documento="CC",
        documento_identidad=documento,
        email=email,
        contrasena=_hash_contrasena("Clave123*"),
        rol=rol,
        activo=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def escenario(db):
    """
    Los mismos datos del Figma: Ana Torres (docente), Lucía Martínez (estudiante)
    y el curso "Diseño de interfaces con Figma" con una lección y su evaluación.
    """
    admin = crear_usuario(db, "admin", "admin@campus.co", "100", "Admin")
    docente = crear_usuario(db, "Ana Torres", "ana.torres@campus.co", "200", "Docente")
    estudiante = crear_usuario(db, "Lucía Martínez", "lucia.martinez@email.com", "300", "Estudiante")

    categoria = Categoria(nombre_categoria="Diseño digital", id_usuario_creacion=admin.id_usuario)
    db.add(categoria)
    db.commit()

    curso = Curso(
        id_categoria=categoria.id_categoria,
        nombre_curso="Diseño de interfaces con Figma",
        descripcion_curso="De tu primera idea a un prototipo",
        duracion_horas=12,
        estado_curso="PUBLICADO",
        precio=120.0,
        id_docente=docente.id_usuario,
        id_usuario_creacion=docente.id_usuario,
    )
    db.add(curso)
    db.commit()

    leccion = Leccion(
        id_curso=curso.id_curso,
        titulo_leccion="Jerarquía visual",
        orden=1,
        duracion_horas=1,
        id_usuario_creacion=docente.id_usuario,
    )
    db.add(leccion)
    db.commit()

    evaluacion = Evaluacion(
        id_leccion=leccion.id_leccion,
        nombre_evaluacion="Cuestionario 1",
        porcentaje=100,
        nota_minima=3.0,
        id_usuario_creacion=docente.id_usuario,
    )
    db.add(evaluacion)
    db.commit()

    inscripcion = Inscripcion(
        id_curso=curso.id_curso,
        id_usuario_inscrito=estudiante.id_usuario,
        estado_inscripcion=EstadoInscripcion.ACTIVA.value,
        id_usuario_creacion=estudiante.id_usuario,
    )
    db.add(inscripcion)
    db.commit()

    return {
        "admin": admin,
        "docente": docente,
        "estudiante": estudiante,
        "categoria": categoria,
        "curso": curso,
        "leccion": leccion,
        "evaluacion": evaluacion,
        "inscripcion": inscripcion,
    }
