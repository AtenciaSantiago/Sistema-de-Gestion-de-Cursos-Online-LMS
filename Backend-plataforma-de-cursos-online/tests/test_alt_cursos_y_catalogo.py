"""
Entregable 3 - Flujos alternativos y excepciones.
EP-02 Administración y catálogo: cursos y categorías (HU-04), publicación (HU-05), catálogo (HU-06) y cursos asignados (HU-07).

Cada prueba cita la historia y el escenario, y afirma el código HTTP, el mensaje exacto y,
cuando aplica, lo que quedó en la base de datos. Las transiciones de la inscripción están en
test_maquina_estados_inscripcion.py y aquí no se repiten.
"""


import pytest

from conftest import crear_usuario, token_de
from src.entities.Curso import Curso
from src.entities.Evaluacion import Evaluacion
from src.entities.Leccion import Leccion
from src.entities.Material import Material
from src.entities.categoria import Categoria
from src.entities.inscripcion import EstadoInscripcion, Inscripcion
from src.entities.pregunta import Pregunta
from src.services.curso import MENSAJE_NO_PUBLICABLE
from src.services.permisos import MENSAJE_NO_ES_SU_CURSO

MENSAJE_CAMPOS_OBLIGATORIOS = "Por favor complete todos los campos obligatorios"  # src/app.py
ID_INEXISTENTE = "00000000-0000-0000-0000-000000000000"


# ------------------------------ Ayudas ------------------------------------
def _docente2(db):
    return crear_usuario(db, "Carlos Ruiz", "carlos.ruiz@campus.co", "400", "Docente")


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


def _leccion(db, escenario, curso=None, orden=2, titulo="Color"):
    leccion = Leccion(id_curso=(curso or escenario["curso"]).id_curso, titulo_leccion=titulo, orden=orden,
                      duracion_horas=1, id_usuario_creacion=escenario["docente"].id_usuario)
    db.add(leccion)
    db.commit()
    return leccion


# =============================== HU-04 ===================================
def test_editar_un_curso_con_un_campo_obligatorio_vacio(cliente, db, escenario):
    """HU-04 esc. 4 (en la edición): dejar la descripción vacía -> 422, campo marcado y el curso no cambia."""
    curso = escenario["curso"]
    r = cliente.put(f"/cursos/{curso.id_curso}", headers=token_de(escenario["docente"]), json={"descripcion_curso": ""})
    assert r.status_code == 422
    assert r.json()["detail"] == MENSAJE_CAMPOS_OBLIGATORIOS
    assert r.json()["campos"] == ["descripcion_curso"]
    db.refresh(curso)
    assert curso.descripcion_curso == "De tu primera idea a un prototipo"


def test_crear_un_curso_con_nombre_repetido(cliente, db, escenario):
    """Integridad (HU-04): no pueden existir dos cursos con el mismo nombre."""
    r = cliente.post("/cursos", headers=token_de(escenario["docente"]), json={
        "id_categoria": str(escenario["categoria"].id_categoria), "nombre_curso": "Diseño de interfaces con Figma",
        "descripcion_curso": "Otro igual", "duracion_horas": 8, "precio": 50,
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "El curso ya existe"
    assert db.query(Curso).count() == 1


def test_crear_un_curso_en_una_categoria_que_no_existe(cliente, db, escenario):
    """Integridad (HU-04): la categoría del curso debe existir."""
    r = cliente.post("/cursos", headers=token_de(escenario["docente"]), json={
        "id_categoria": ID_INEXISTENTE, "nombre_curso": "UX Writing",
        "descripcion_curso": "Textos claros", "duracion_horas": 8, "precio": 50,
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "La categoría no existe"
    assert db.query(Curso).count() == 1


def test_crear_una_categoria_repetida(cliente, db, escenario):
    """Integridad (HU-04): la categoría no se repite aunque cambien mayúsculas o espacios."""
    r = cliente.post("/categorias", headers=token_de(escenario["admin"]), json={"nombre_categoria": "  diseño DIGITAL "})
    assert r.status_code == 400
    assert r.json()["detail"] == "La categoría ya existe"
    assert db.query(Categoria).count() == 1


def test_no_se_elimina_una_categoria_con_cursos(cliente, db, escenario):
    """Integridad: la categoría con cursos asociados no se borra (antes era un error 500)."""
    categoria = escenario["categoria"]
    r = cliente.delete(f"/categorias/{categoria.id_categoria}", headers=token_de(escenario["admin"]))
    assert r.status_code == 400
    assert r.json()["detail"] == "No se puede eliminar la categoría porque tiene cursos asociados"
    db.expire_all()
    assert db.query(Categoria).count() == 1


MENSAJE_CURSO_CON_DATOS = (
    "El curso tiene lecciones o estudiantes inscritos y no se puede eliminar. Páselo a BORRADOR para ocultarlo"
)


def test_no_se_elimina_un_curso_con_lecciones(cliente, db, escenario):
    """Integridad: un curso que ya tiene lecciones no se borra."""
    curso = _curso(db, escenario, "Curso con lección", estado="BORRADOR")
    _leccion(db, escenario, curso=curso, orden=1)
    r = cliente.delete(f"/cursos/{curso.id_curso}", headers=token_de(escenario["admin"]))
    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_CURSO_CON_DATOS
    db.expire_all()
    assert db.query(Curso).filter(Curso.id_curso == curso.id_curso).count() == 1


def test_no_se_elimina_un_curso_con_estudiantes_inscritos(cliente, db, escenario):
    """Integridad: un curso con inscritos (aunque no tenga lecciones) no se borra."""
    curso = _curso(db, escenario, "Curso con inscrito", estado="BORRADOR")
    db.add(Inscripcion(id_curso=curso.id_curso, id_usuario_inscrito=escenario["estudiante"].id_usuario,
                       estado_inscripcion=EstadoInscripcion.ACTIVA.value,
                       id_usuario_creacion=escenario["admin"].id_usuario))
    db.commit()
    r = cliente.delete(f"/cursos/{curso.id_curso}", headers=token_de(escenario["admin"]))
    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_CURSO_CON_DATOS
    db.expire_all()
    assert db.query(Curso).filter(Curso.id_curso == curso.id_curso).count() == 1


# =============================== HU-05 ===================================
def test_no_se_publica_un_curso_sin_profesor_asignado(cliente, db, escenario):
    """HU-05 esc. 3 (datos incompletos): con lección pero sin profesor, el curso no se publica y sigue en BORRADOR."""
    curso = _curso(db, escenario, "Curso sin profesor", estado="BORRADOR", docente=None)
    _leccion(db, escenario, curso=curso, orden=1)
    r = cliente.put(f"/cursos/{curso.id_curso}", headers=token_de(escenario["admin"]), json={"estado_curso": "PUBLICADO"})
    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_NO_PUBLICABLE
    db.refresh(curso)
    assert curso.estado_curso == "BORRADOR"


def test_docente_no_publica_ni_oculta_mensaje_exacto(cliente, db, escenario):
    """HU-05: el docente no cambia el estado de su propio curso; mensaje exacto y el curso sigue PUBLICADO."""
    curso = escenario["curso"]
    r = cliente.put(f"/cursos/{curso.id_curso}", headers=token_de(escenario["docente"]), json={"estado_curso": "BORRADOR"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Solo el administrador puede publicar u ocultar un curso"
    db.refresh(curso)
    assert curso.estado_curso == "PUBLICADO"


# =============================== HU-06 ===================================
def test_catalogo_filtra_por_categoria(cliente, db, escenario):
    """HU-06 esc. 2: con ?id_categoria= solo salen los cursos publicados de esa categoría."""
    otra = Categoria(nombre_categoria="Programación", id_usuario_creacion=escenario["admin"].id_usuario)
    db.add(otra)
    db.commit()
    _curso(db, escenario, "Python desde cero", categoria=otra)

    todos = cliente.get("/catalogo").json()
    filtrado = cliente.get("/catalogo", params={"id_categoria": str(otra.id_categoria)})

    assert len(todos) == 2
    assert filtrado.status_code == 200
    assert [c["nombre_curso"] for c in filtrado.json()] == ["Python desde cero"]


def test_catalogo_de_una_categoria_sin_cursos_publicados_sale_vacio(cliente, db, escenario):
    """HU-06 esc. 3: la categoría solo tiene un curso en BORRADOR -> 200 y lista vacía (el mensaje lo pone el frontend)."""
    otra = Categoria(nombre_categoria="Programación", id_usuario_creacion=escenario["admin"].id_usuario)
    db.add(otra)
    db.commit()
    _curso(db, escenario, "Python desde cero", estado="BORRADOR", categoria=otra)

    r = cliente.get("/catalogo", params={"id_categoria": str(otra.id_categoria)})

    assert r.status_code == 200
    assert r.json() == []


# =============================== HU-07 ===================================
def test_docente_ve_las_lecciones_de_su_curso_asignado(cliente, db, escenario):
    """HU-07 esc. 3: al entrar a la gestión del curso, el docente recibe sus lecciones en orden."""
    _leccion(db, escenario, orden=2, titulo="Color")
    r = cliente.get("/lecciones", headers=token_de(escenario["docente"]),
                    params={"id_curso": str(escenario["curso"].id_curso)})
    assert r.status_code == 200
    assert [(l["orden"], l["titulo_leccion"]) for l in r.json()] == [(1, "Jerarquía visual"), (2, "Color")]


def test_docente_no_ve_las_lecciones_de_un_curso_ajeno(cliente, db, escenario):
    """HU-07 esc. 3 / RN-02: si pide las lecciones de un curso que no es suyo recibe la lista vacía y el detalle da 404."""
    otro = _docente2(db)
    lista = cliente.get("/lecciones", headers=token_de(otro), params={"id_curso": str(escenario["curso"].id_curso)})
    assert lista.status_code == 200
    assert lista.json() == []
    detalle = cliente.get(f"/lecciones/{escenario['leccion'].id_leccion}", headers=token_de(otro))
    assert detalle.status_code == 404
    assert detalle.json()["detail"] == "Lección no encontrada"


@pytest.mark.parametrize("recurso", ["curso", "leccion", "material", "evaluacion", "pregunta"])
def test_docente_no_modifica_el_contenido_de_un_curso_ajeno(cliente, db, escenario, recurso):
    """RN-02 (transversal): curso, lección, material, evaluación y preguntas de otro docente -> 403 con el mensaje exacto."""
    otro = token_de(_docente2(db))
    if recurso == "curso":
        r = cliente.put(f"/cursos/{escenario['curso'].id_curso}", headers=otro, json={"duracion_horas": 1})
    elif recurso == "leccion":
        r = cliente.put(f"/lecciones/{escenario['leccion'].id_leccion}", headers=otro, json={"titulo_leccion": "Ajena"})
    elif recurso == "material":
        r = cliente.post("/material", headers=otro, json={
            "id_leccion": str(escenario["leccion"].id_leccion), "titulo_material": "Guía",
            "tipo_material": "PDF", "URL_archivo": "https://campus.co/guia.pdf"})
    elif recurso == "evaluacion":
        r = cliente.put(f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}", headers=otro,
                        json={"nombre_evaluacion": "Ajena"})
    else:
        r = cliente.post(f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/preguntas", headers=otro,
                         json={"tipo": "VERDADERO_FALSO", "enunciado": "x", "respuesta_correcta": "Verdadero"})
    assert r.status_code == 403
    assert r.json()["detail"] == MENSAJE_NO_ES_SU_CURSO
    db.expire_all()
    assert db.query(Material).count() == 0 and db.query(Pregunta).count() == 0
    assert db.query(Leccion).one().titulo_leccion == "Jerarquía visual"
    assert db.query(Evaluacion).one().nombre_evaluacion == "Cuestionario 1"
    assert db.query(Curso).one().duracion_horas == 12
