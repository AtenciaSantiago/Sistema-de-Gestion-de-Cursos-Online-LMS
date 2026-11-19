"""
Pruebas del aula virtual y del progreso (HU-11 y HU-12).
"""

from conftest import token_de
from src.entities.Curso import Curso
from src.entities.Leccion import Leccion
from src.entities.Material import Material


def _segunda_leccion(db, escenario):
    leccion = Leccion(
        id_curso=escenario["curso"].id_curso,
        titulo_leccion="Componentes y estilos reutilizables",  # más de 20 caracteres: antes fallaba en PostgreSQL
        orden=2,
        duracion_horas=1,
        id_usuario_creacion=escenario["docente"].id_usuario,
    )
    db.add(leccion)
    db.add(Material(
        id_leccion=escenario["leccion"].id_leccion, titulo_material="Guía de jerarquía visual",
        tipo_material="PDF", URL_archivo="https://ejemplo.com/guia.pdf", id_usuario_creacion=escenario["docente"].id_usuario,
    ))
    db.commit()
    return leccion


def test_dos_cursos_pueden_tener_su_leccion_1(db, escenario):
    """Antes el orden era único en toda la base y esto fallaba."""
    otro = Curso(
        id_categoria=escenario["categoria"].id_categoria, nombre_curso="Otro curso", duracion_horas=4,
        estado_curso="PUBLICADO", precio=10, id_usuario_creacion=escenario["docente"].id_usuario,
    )
    db.add(otro)
    db.commit()
    db.add(Leccion(id_curso=otro.id_curso, titulo_leccion="Intro", orden=1, duracion_horas=1,
                   id_usuario_creacion=escenario["docente"].id_usuario))
    db.commit()  # no lanza error


def test_contenido_en_orden_con_materiales_y_evaluacion(cliente, db, escenario):
    _segunda_leccion(db, escenario)
    r = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["estudiante"]))
    assert r.status_code == 200, r.text
    contenido = r.json()
    assert [l["orden"] for l in contenido["lecciones"]] == [1, 2]
    assert contenido["lecciones"][0]["materiales"][0]["titulo_material"] == "Guía de jerarquía visual"
    assert contenido["lecciones"][0]["evaluacion"]["nombre_evaluacion"] == "Cuestionario 1"
    assert contenido["porcentaje_avance"] == 0


def test_marcar_completada_actualiza_el_avance(cliente, db, escenario):
    _segunda_leccion(db, escenario)
    r = cliente.post(f"/mis-cursos/lecciones/{escenario['leccion'].id_leccion}/completar", headers=token_de(escenario["estudiante"]))
    assert r.json()["porcentaje_avance"] == 50
    # marcarla dos veces no duplica
    r = cliente.post(f"/mis-cursos/lecciones/{escenario['leccion'].id_leccion}/completar", headers=token_de(escenario["estudiante"]))
    assert r.json()["porcentaje_avance"] == 50


def test_mis_cursos_lista_el_curso_con_su_avance(cliente, escenario):
    r = cliente.get("/mis-cursos", headers=token_de(escenario["estudiante"]))
    cursos = r.json()
    assert cursos[0]["nombre_curso"] == "Diseño de interfaces con Figma"
    assert cursos[0]["estado_inscripcion"] == "ACTIVA"


def test_inscripcion_pendiente_no_ve_el_contenido(cliente, db, escenario):
    escenario["inscripcion"].estado_inscripcion = "PENDIENTE"
    db.commit()
    r = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["estudiante"]))
    assert r.status_code == 403
    assert "No cuenta con una inscripción activa" in r.json()["detail"]
