"""
Entregable 3 - Flujos alternativos y excepciones.
EP-05 Evaluación y certificación: certificado (HU-13), diseño de evaluaciones (HU-14) y presentación (HU-15).

Cada prueba cita la historia y el escenario, y afirma el código HTTP, el mensaje exacto y,
cuando aplica, lo que quedó en la base de datos. Las transiciones de la inscripción están en
test_maquina_estados_inscripcion.py y aquí no se repiten.
"""


import pytest

from conftest import token_de
from src.entities.Evaluacion import Evaluacion
from src.entities.Leccion import Leccion
from src.entities.inscripcion import EstadoInscripcion, Inscripcion
from src.entities.intento_evaluacion import IntentoEvaluacion
from src.entities.pregunta import Pregunta
from src.patrones.factory_preguntas import MENSAJE_CLAVE_INVALIDA
from src.services.certificado import MENSAJE_NO_CUMPLE
from src.services.presentacion_evaluacion import MENSAJE_YA_APROBADA

MENSAJE_CAMPOS_OBLIGATORIOS = "Por favor complete todos los campos obligatorios"  # src/app.py
ID_INEXISTENTE = "00000000-0000-0000-0000-000000000000"


# ------------------------------ Ayudas ------------------------------------


def _leccion(db, escenario, curso=None, orden=2, titulo="Color"):
    leccion = Leccion(id_curso=(curso or escenario["curso"]).id_curso, titulo_leccion=titulo, orden=orden,
                      duracion_horas=1, id_usuario_creacion=escenario["docente"].id_usuario)
    db.add(leccion)
    db.commit()
    return leccion


def _pregunta_vf(cliente, escenario, clave="Verdadero"):
    r = cliente.post(
        f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/preguntas",
        headers=token_de(escenario["docente"]),
        json={"tipo": "VERDADERO_FALSO", "enunciado": "El contraste ayuda.", "respuesta_correcta": clave},
    )
    assert r.status_code == 201, r.text
    return r.json()["id_pregunta"]


def _presentar(cliente, escenario, respuestas):
    return cliente.post(
        f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/presentar",
        headers=token_de(escenario["estudiante"]),
        json={"respuestas": respuestas},
    )


# =============================== HU-13 ===================================
def test_inscripcion_cancelada_no_descarga_certificado(cliente, db, escenario):
    """HU-13 esc. 3: con la inscripción CANCELADA no hay certificado (403 y el mensaje del escenario)."""
    escenario["inscripcion"].estado_inscripcion = EstadoInscripcion.CANCELADA.value
    db.commit()
    r = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}/certificado", headers=token_de(escenario["estudiante"]))
    assert r.status_code == 403
    assert r.json()["detail"] == MENSAJE_NO_CUMPLE


# =============================== HU-14 ===================================
def test_editar_la_nota_minima_de_una_evaluacion_no_presentada(cliente, db, escenario):
    """HU-14 esc. 2: mientras nadie la haya presentado, el docente cambia la nota mínima."""
    evaluacion = escenario["evaluacion"]
    r = cliente.put(f"/evaluaciones/{evaluacion.id_evaluacion}", headers=token_de(escenario["docente"]), json={"nota_minima": 4.0})
    assert r.status_code == 200, r.text
    assert r.json()["nota_minima"] == 4.0
    db.refresh(evaluacion)
    assert evaluacion.nota_minima == 4.0


def test_editar_la_clave_de_una_pregunta_no_presentada(cliente, db, escenario):
    """HU-14 esc. 2: mientras nadie la haya presentado, el docente corrige la respuesta correcta."""
    id_pregunta = _pregunta_vf(cliente, escenario, clave="Verdadero")
    r = cliente.put(f"/preguntas/{id_pregunta}", headers=token_de(escenario["docente"]), json={"respuesta_correcta": "Falso"})
    assert r.status_code == 200, r.text
    assert r.json()["respuesta_correcta"] == "Falso"
    db.expire_all()
    assert db.query(Pregunta).one().respuesta_correcta == "Falso"


@pytest.mark.parametrize("cuerpo", [
    {"tipo": "OPCION_MULTIPLE", "enunciado": "¿Cuál?", "opciones": ["A", "B"], "respuesta_correcta": "C"},
    {"tipo": "OPCION_MULTIPLE", "enunciado": "¿Cuál?", "opciones": ["A", "B"], "respuesta_correcta": ""},
    {"tipo": "VERDADERO_FALSO", "enunciado": "¿Sí?", "respuesta_correcta": "Tal vez"},
], ids=["clave_fuera_de_las_opciones", "clave_vacia", "verdadero_falso_con_otra_clave"])
def test_pregunta_con_clave_invalida_por_la_api(cliente, db, escenario, cuerpo):
    """HU-14 esc. 3: sin una respuesta correcta válida la pregunta no se guarda (400 y el mensaje de la HU)."""
    r = cliente.post(f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/preguntas",
                     headers=token_de(escenario["docente"]), json=cuerpo)
    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_CLAVE_INVALIDA
    assert db.query(Pregunta).count() == 0


def test_pregunta_sin_el_campo_de_la_clave_responde_422(cliente, db, escenario):
    """
    HU-14 esc. 3, tal como es HOY: si el campo respuesta_correcta no se envía, la API responde 422 con el
    mensaje general de campos obligatorios (no el mensaje de la HU, que solo sale con la clave vacía o inválida).
    """
    r = cliente.post(f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/preguntas",
                     headers=token_de(escenario["docente"]),
                     json={"tipo": "VERDADERO_FALSO", "enunciado": "¿Sí?"})
    assert r.status_code == 422
    assert r.json()["detail"] == MENSAJE_CAMPOS_OBLIGATORIOS
    assert r.json()["campos"] == ["respuesta_correcta"]
    assert db.query(Pregunta).count() == 0


def test_editar_la_clave_a_un_valor_invalido(cliente, db, escenario):
    """HU-14 esc. 3 (en la edición): cambiar la clave por un valor inválido se rechaza y la clave no cambia."""
    id_pregunta = _pregunta_vf(cliente, escenario, clave="Verdadero")
    r = cliente.put(f"/preguntas/{id_pregunta}", headers=token_de(escenario["docente"]), json={"respuesta_correcta": "Quizás"})
    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_CLAVE_INVALIDA
    db.expire_all()
    assert db.query(Pregunta).one().respuesta_correcta == "Verdadero"


def test_crear_una_evaluacion_con_nota_minima_fuera_de_rango(cliente, db, escenario):
    """HU-14 esc. 3 (al crear): la nota de aprobación debe estar entre 0 y 5."""
    leccion = _leccion(db, escenario, orden=2)
    escenario["evaluacion"].porcentaje = 50  # preparación: deja cupo de porcentaje en el curso
    db.commit()
    r = cliente.post("/evaluaciones", headers=token_de(escenario["docente"]), json={
        "id_leccion": str(leccion.id_leccion), "nombre_evaluacion": "Taller", "porcentaje": 50, "nota_minima": 6})
    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_CLAVE_INVALIDA
    assert db.query(Evaluacion).count() == 1


def test_segunda_evaluacion_en_la_misma_leccion(cliente, db, escenario):
    """HU-14 / RN-03 (ajuste E2): cada lección admite una sola evaluación."""
    escenario["evaluacion"].porcentaje = 50  # preparación: que no choque con la regla del 100 %
    db.commit()
    r = cliente.post("/evaluaciones", headers=token_de(escenario["docente"]), json={
        "id_leccion": str(escenario["leccion"].id_leccion), "nombre_evaluacion": "Otra", "porcentaje": 50})
    assert r.status_code == 400
    assert r.json()["detail"] == "Esta lección ya tiene una evaluación"
    assert db.query(Evaluacion).count() == 1


@pytest.mark.parametrize("cuerpo, mensaje", [
    ({"tipo": "VERDADERO_FALSO", "enunciado": "  ", "respuesta_correcta": "Verdadero"}, "La pregunta debe tener un enunciado"),
    ({"tipo": "OPCION_MULTIPLE", "enunciado": "¿Cuál?", "opciones": ["A"], "respuesta_correcta": "A"},
     "Una pregunta de opción múltiple necesita al menos 2 opciones"),
    ({"tipo": "OPCION_MULTIPLE", "enunciado": "¿Cuál?", "opciones": ["A", "A"], "respuesta_correcta": "A"},
     "Las opciones de la pregunta no se pueden repetir"),
    ({"tipo": "ABIERTA", "enunciado": "¿Cuál?", "respuesta_correcta": "A"}, "Tipo de pregunta no soportado: ABIERTA"),
], ids=["sin_enunciado", "una_sola_opcion", "opciones_repetidas", "tipo_desconocido"])
def test_pregunta_mal_armada_por_la_api(cliente, db, escenario, cuerpo, mensaje):
    """HU-14 (ajuste E2): la Factory rechaza la pregunta mal armada; por la API es 400 con su mensaje."""
    r = cliente.post(f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/preguntas",
                     headers=token_de(escenario["docente"]), json=cuerpo)
    assert r.status_code == 400
    assert r.json()["detail"] == mensaje
    assert db.query(Pregunta).count() == 0


# =============================== HU-15 ===================================
def test_evaluacion_reprobada_mensaje_exacto(cliente, db, escenario):
    """HU-15 esc. 2: al no alcanzar la nota mínima se informa con el mensaje del E1 y se guarda el intento."""
    id_pregunta = _pregunta_vf(cliente, escenario)
    r = _presentar(cliente, escenario, {id_pregunta: "Falso"})
    assert r.status_code == 200, r.text
    assert r.json()["aprobada"] is False
    assert r.json()["mensaje"] == "No alcanzaste la nota mínima requerida. Puedes volver a intentarlo."
    assert [(i.numero_intento, i.nota) for i in db.query(IntentoEvaluacion).all()] == [(1, 0.0)]


def test_reenviar_una_evaluacion_aprobada_mensaje_exacto(cliente, db, escenario):
    """HU-15 esc. 3: la evaluación ya aprobada queda en solo lectura; el reenvío no guarda otro intento."""
    _leccion(db, escenario, orden=2)  # queda una lección pendiente: la inscripción sigue ACTIVA
    id_pregunta = _pregunta_vf(cliente, escenario)
    assert _presentar(cliente, escenario, {id_pregunta: "Verdadero"}).json()["aprobada"] is True

    r = _presentar(cliente, escenario, {id_pregunta: "Falso"})

    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_YA_APROBADA
    db.expire_all()
    assert db.query(IntentoEvaluacion).count() == 1
    assert db.query(Inscripcion).one().estado_inscripcion == EstadoInscripcion.ACTIVA.value


def test_presentar_una_evaluacion_sin_preguntas(cliente, db, escenario):
    """HU-15 (ajuste E2): una evaluación sin preguntas no se puede presentar ni deja intento."""
    r = _presentar(cliente, escenario, {})
    assert r.status_code == 400
    assert r.json()["detail"] == "La evaluación todavía no tiene preguntas"
    assert db.query(IntentoEvaluacion).count() == 0


def test_presentar_una_evaluacion_que_no_existe(cliente, escenario):
    """HU-15 (ajuste E2), tal como es HOY: la evaluación inexistente responde 400 (no 404) con su mensaje."""
    r = cliente.post(f"/evaluaciones/{ID_INEXISTENTE}/presentar", headers=token_de(escenario["estudiante"]),
                     json={"respuestas": {}})
    assert r.status_code == 400
    assert r.json()["detail"] == "La evaluación no existe"
