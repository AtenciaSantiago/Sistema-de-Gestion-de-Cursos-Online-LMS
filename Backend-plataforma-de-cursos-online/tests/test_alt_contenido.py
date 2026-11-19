"""
Entregable 3 - Flujos alternativos y excepciones.
EP-04 Contenido y aprendizaje: lecciones y materiales (HU-11) y aula virtual (HU-12).

Cada prueba cita la historia y el escenario, y afirma el código HTTP, el mensaje exacto y,
cuando aplica, lo que quedó en la base de datos. Las transiciones de la inscripción están en
test_maquina_estados_inscripcion.py y aquí no se repiten.
"""


import pytest

from conftest import token_de
from src.entities.Evaluacion import Evaluacion
from src.entities.Leccion import Leccion
from src.entities.Material import Material
from src.entities.progreso_leccion import ProgresoLeccion

ID_INEXISTENTE = "00000000-0000-0000-0000-000000000000"


# ------------------------------ Ayudas ------------------------------------


def _leccion(db, escenario, curso=None, orden=2, titulo="Color"):
    leccion = Leccion(id_curso=(curso or escenario["curso"]).id_curso, titulo_leccion=titulo, orden=orden,
                      duracion_horas=1, id_usuario_creacion=escenario["docente"].id_usuario)
    db.add(leccion)
    db.commit()
    return leccion


# =============================== HU-11 ===================================
def test_reordenar_una_leccion_a_un_orden_libre(cliente, db, escenario):
    """HU-11 esc. 3 (camino exitoso): mover la lección a un número de orden libre guarda el nuevo orden."""
    leccion = escenario["leccion"]
    r = cliente.put(f"/lecciones/{leccion.id_leccion}", headers=token_de(escenario["docente"]), json={"orden": 3})
    assert r.status_code == 200, r.text
    assert r.json()["orden"] == 3
    db.refresh(leccion)
    assert leccion.orden == 3


def test_material_con_tipo_no_permitido(cliente, db, escenario):
    """HU-11 (ajuste E2): el tipo de material debe ser PDF, VIDEO, DOCUMENTO o ENLACE."""
    r = cliente.post("/material", headers=token_de(escenario["docente"]), json={
        "id_leccion": str(escenario["leccion"].id_leccion), "titulo_material": "Podcast",
        "tipo_material": "AUDIO", "URL_archivo": "https://campus.co/audio.mp3"})
    assert r.status_code == 400
    assert r.json()["detail"] == "El tipo de material debe ser PDF, VIDEO, DOCUMENTO o ENLACE"
    assert db.query(Material).count() == 0


def test_material_en_una_leccion_que_no_existe(cliente, db, escenario):
    """HU-11 / RN-03: un material siempre cuelga de una lección que existe."""
    r = cliente.post("/material", headers=token_de(escenario["docente"]), json={
        "id_leccion": ID_INEXISTENTE, "titulo_material": "Guía",
        "tipo_material": "PDF", "URL_archivo": "https://campus.co/guia.pdf"})
    assert r.status_code == 400
    assert r.json()["detail"] == "La lección no existe"
    assert db.query(Material).count() == 0


@pytest.mark.parametrize("contenido", ["material", "evaluacion", "avance"])
def test_no_se_elimina_una_leccion_con_contenido(cliente, db, escenario, contenido):
    """Integridad / RN-03: la lección con material, evaluación o avance de estudiantes no se borra."""
    leccion = _leccion(db, escenario, orden=2)  # segunda lección: así no choca con la regla de la HU-05
    if contenido == "material":
        db.add(Material(id_leccion=leccion.id_leccion, titulo_material="Guía", tipo_material="PDF",
                        URL_archivo="https://campus.co/guia.pdf", id_usuario_creacion=escenario["docente"].id_usuario))
    elif contenido == "evaluacion":
        db.add(Evaluacion(id_leccion=leccion.id_leccion, nombre_evaluacion="Taller", porcentaje=0, nota_minima=3.0,
                          id_usuario_creacion=escenario["docente"].id_usuario))
    else:
        db.add(ProgresoLeccion(id_inscripcion=escenario["inscripcion"].id_inscripcion, id_leccion=leccion.id_leccion))
    db.commit()

    r = cliente.delete(f"/lecciones/{leccion.id_leccion}", headers=token_de(escenario["docente"]))

    assert r.status_code == 400
    assert r.json()["detail"] == "La lección tiene materiales, evaluación o avance de estudiantes y no se puede eliminar"
    db.expire_all()
    assert db.query(Leccion).filter(Leccion.id_leccion == leccion.id_leccion).count() == 1


# =============================== HU-12 ===================================
def test_el_aula_entrega_el_enlace_del_material(cliente, db, escenario):
    """HU-12 esc. 3: el aula trae el enlace y el tipo del material para abrirlo (abrir la pestaña es del frontend)."""
    db.add(Material(id_leccion=escenario["leccion"].id_leccion, titulo_material="Guía de jerarquía", tipo_material="PDF",
                    URL_archivo="https://campus.co/guia.pdf", id_usuario_creacion=escenario["docente"].id_usuario))
    db.commit()
    aula = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["estudiante"]))
    assert aula.status_code == 200
    materiales = aula.json()["lecciones"][0]["materiales"]
    assert [(m["titulo_material"], m["tipo_material"], m["URL_archivo"]) for m in materiales] == [
        ("Guía de jerarquía", "PDF", "https://campus.co/guia.pdf")
    ]
