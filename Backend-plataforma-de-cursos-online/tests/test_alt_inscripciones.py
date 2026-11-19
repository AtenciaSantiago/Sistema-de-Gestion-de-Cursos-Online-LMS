"""
Entregable 3 - Flujos alternativos y excepciones.
EP-03 Pagos e inscripciones: matrícula manual y cancelación por el administrador (RF-10).

Cada prueba cita la historia y el escenario, y afirma el código HTTP, el mensaje exacto y,
cuando aplica, lo que quedó en la base de datos. Las transiciones de la inscripción están en
test_maquina_estados_inscripcion.py y aquí no se repiten.
"""


import pytest

from conftest import crear_usuario, token_de
from src.endpoints.deps import MENSAJE_SIN_PERMISO
from src.entities.Curso import Curso
from src.entities.inscripcion import EstadoInscripcion, Inscripcion

ID_INEXISTENTE = "00000000-0000-0000-0000-000000000000"


# ------------------------------ Ayudas ------------------------------------
def _docente2(db):
    return crear_usuario(db, "Carlos Ruiz", "carlos.ruiz@campus.co", "400", "Docente")


def _estudiante2(db):
    return crear_usuario(db, "Pedro Gil", "pedro@email.com", "500", "Estudiante")


def _curso(db, escenario, nombre, estado="PUBLICADO", categoria=None, docente="escenario"):
    """Curso creado directo en la base (preparación)."""
    curso = Curso(
        id_categoria=(categoria or escenario["categoria"]).id_categoria,
        nombre_curso=nombre,
        descripcion_curso="Curso de apoyo para la prueba",
        duracion_horas=4,
        estado_curso=estado,
        precio=80.0,
        id_docente=escenario["docente"].id_usuario if docente == "escenario" else docente,
        id_usuario_creacion=escenario["admin"].id_usuario,
    )
    db.add(curso)
    db.commit()
    return curso


# =============================== RF-10 ===================================
@pytest.mark.parametrize("caso", ["docente", "estudiante_inactivo", "usuario_inexistente"])
def test_matricula_manual_solo_para_estudiantes_activos(cliente, db, escenario, caso):
    """RF-10: el administrador solo matricula usuarios activos con rol Estudiante."""
    if caso == "docente":
        id_usuario = _docente2(db).id_usuario
    elif caso == "estudiante_inactivo":
        pedro = _estudiante2(db)
        pedro.activo = False
        db.commit()
        id_usuario = pedro.id_usuario
    else:
        id_usuario = ID_INEXISTENTE
    r = cliente.post("/inscripciones", headers=token_de(escenario["admin"]),
                     json={"id_curso": str(escenario["curso"].id_curso), "id_usuario_inscrito": str(id_usuario)})
    assert r.status_code == 400
    assert r.json()["detail"] == "Solo se pueden matricular usuarios activos con rol Estudiante"
    assert db.query(Inscripcion).count() == 1  # solo la de Lucía


def test_matricula_manual_en_un_curso_no_publicado(cliente, db, escenario):
    """RF-10: no se matricula a nadie en un curso que no está PUBLICADO."""
    curso = _curso(db, escenario, "En borrador", estado="BORRADOR")
    pedro = _estudiante2(db)
    r = cliente.post("/inscripciones", headers=token_de(escenario["admin"]),
                     json={"id_curso": str(curso.id_curso), "id_usuario_inscrito": str(pedro.id_usuario)})
    assert r.status_code == 400
    assert r.json()["detail"] == "El curso no existe o no está publicado"
    assert db.query(Inscripcion).filter(Inscripcion.id_usuario_inscrito == pedro.id_usuario).count() == 0


def test_cancelar_una_inscripcion_que_no_existe(cliente, escenario):
    """RF-10: cancelar una inscripción inexistente responde 404."""
    r = cliente.put(f"/inscripciones/{ID_INEXISTENTE}/cancelar", headers=token_de(escenario["admin"]))
    assert r.status_code == 404
    assert r.json()["detail"] == "Inscripción no encontrada"


@pytest.mark.parametrize("rol", ["docente", "estudiante"])
def test_solo_el_admin_cancela_inscripciones(cliente, db, escenario, rol):
    """RF-10 / RN-02: ni el docente ni el propio estudiante pueden cancelar; la inscripción sigue ACTIVA."""
    inscripcion = escenario["inscripcion"]
    r = cliente.put(f"/inscripciones/{inscripcion.id_inscripcion}/cancelar", headers=token_de(escenario[rol]))
    assert r.status_code == 403
    assert r.json()["detail"] == MENSAJE_SIN_PERMISO
    db.refresh(inscripcion)
    assert inscripcion.estado_inscripcion == EstadoInscripcion.ACTIVA.value
