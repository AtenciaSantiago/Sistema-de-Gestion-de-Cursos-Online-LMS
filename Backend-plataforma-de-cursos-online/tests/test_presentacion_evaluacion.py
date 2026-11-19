"""
Pruebas del flujo HU-14 + HU-15 contra la API:
el docente arma la evaluación y la estudiante la presenta con calificación automática.
"""

from conftest import token_de


def _crear_preguntas(cliente, escenario):
    url = f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/preguntas"
    docente = token_de(escenario["docente"])
    r1 = cliente.post(url, headers=docente, json={
        "tipo": "OPCION_MULTIPLE",
        "enunciado": "¿Qué principio ordena la mirada?",
        "opciones": ["Jerarquía visual", "Color aleatorio", "Texto pequeño"],
        "respuesta_correcta": "Jerarquía visual",
    })
    r2 = cliente.post(url, headers=docente, json={
        "tipo": "VERDADERO_FALSO",
        "enunciado": "El contraste ayuda a destacar la acción principal.",
        "respuesta_correcta": "Verdadero",
    })
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text
    return r1.json(), r2.json()


def test_docente_crea_preguntas_y_estudiante_no_ve_la_clave(cliente, escenario):
    _crear_preguntas(cliente, escenario)
    r = cliente.get(
        f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/preguntas",
        headers=token_de(escenario["estudiante"]),
    )
    assert r.status_code == 200
    preguntas = r.json()
    assert len(preguntas) == 2
    assert all("respuesta_correcta" not in p for p in preguntas)
    assert preguntas[1]["opciones"] == ["Verdadero", "Falso"]


def test_estudiante_no_puede_crear_preguntas(cliente, escenario):
    r = cliente.post(
        f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/preguntas",
        headers=token_de(escenario["estudiante"]),
        json={"tipo": "VERDADERO_FALSO", "enunciado": "x", "respuesta_correcta": "Verdadero"},
    )
    assert r.status_code == 403


def test_presentar_todo_bien_da_cinco_y_aprueba(cliente, escenario):
    p1, p2 = _crear_preguntas(cliente, escenario)
    r = cliente.post(
        f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/presentar",
        headers=token_de(escenario["estudiante"]),
        json={"respuestas": {p1["id_pregunta"]: "Jerarquía visual", p2["id_pregunta"]: "Verdadero"}},
    )
    assert r.status_code == 200, r.text
    resultado = r.json()
    assert resultado["nota"] == 5.0
    assert resultado["aprobada"] is True
    assert resultado["correctas"] == 2


def test_presentar_mitad_bien_da_dos_punto_cinco_y_reprueba(cliente, escenario):
    p1, p2 = _crear_preguntas(cliente, escenario)
    r = cliente.post(
        f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/presentar",
        headers=token_de(escenario["estudiante"]),
        json={"respuestas": {p1["id_pregunta"]: "Jerarquía visual", p2["id_pregunta"]: "Falso"}},
    )
    assert r.json()["nota"] == 2.5
    assert r.json()["aprobada"] is False


def test_sin_inscripcion_activa_no_puede_presentar(cliente, escenario, db):
    p1, p2 = _crear_preguntas(cliente, escenario)
    escenario["inscripcion"].estado_inscripcion = "PENDIENTE"
    db.commit()
    r = cliente.post(
        f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/presentar",
        headers=token_de(escenario["estudiante"]),
        json={"respuestas": {}},
    )
    assert r.status_code == 403
