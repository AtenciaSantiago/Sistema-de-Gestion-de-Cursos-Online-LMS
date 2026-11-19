"""
Entregable 3 - Flujos alternativos y excepciones.
EP-03 Pagos e inscripciones: pago en línea y matrícula automática (HU-09).

Cada prueba cita la historia y el escenario, y afirma el código HTTP, el mensaje exacto y,
cuando aplica, lo que quedó en la base de datos. Las transiciones de la inscripción están en
test_maquina_estados_inscripcion.py y aquí no se repiten.
"""


import pytest

from conftest import crear_usuario, token_de
from src.entities.Curso import Curso
from src.entities.Pago import Pago
from src.entities.inscripcion import Inscripcion

ID_INEXISTENTE = "00000000-0000-0000-0000-000000000000"


# ------------------------------ Ayudas ------------------------------------


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


# =============================== HU-09 ===================================
def test_pago_rechazado_mensaje_exacto_y_pago_guardado(cliente, db, escenario):
    """HU-09 esc. 2: con la pasarela simulada real, el rechazo trae el mensaje del E1 y queda el Pago RECHAZADO."""
    pedro = _estudiante2(db)
    r = cliente.post(f"/checkout/cursos/{escenario['curso'].id_curso}", headers=token_de(pedro),
                     json={"metodo_pago": "TARJETA", "numero_tarjeta": "4000 0000 0000 0002", "titular": "Pedro Gil"})
    assert r.status_code == 200, r.text
    assert r.json()["aprobado"] is False
    assert r.json()["mensaje"] == "Transacción rechazada. Por favor intente con otro método de pago"
    pagos = db.query(Pago).filter(Pago.id_usuario == pedro.id_usuario).all()
    assert [(p.estado_pago, p.metodo_pago, p.monto) for p in pagos] == [("RECHAZADO", "TARJETA", 120.0)]
    assert pagos[0].referencia == r.json()["referencia"]


@pytest.mark.parametrize("estado_curso", ["BORRADOR", "inexistente"])
def test_no_se_paga_un_curso_no_publicado_o_inexistente(cliente, db, escenario, estado_curso):
    """HU-09 (ajuste E2): solo se compra un curso PUBLICADO; no se crea inscripción ni pago."""
    pedro = _estudiante2(db)
    id_curso = ID_INEXISTENTE if estado_curso == "inexistente" else _curso(db, escenario, "En borrador", "BORRADOR").id_curso
    r = cliente.post(f"/checkout/cursos/{id_curso}", headers=token_de(pedro),
                     json={"metodo_pago": "TARJETA", "numero_tarjeta": "4242 4242 4242 4242", "titular": "Pedro Gil"})
    assert r.status_code == 400
    assert r.json()["detail"] == "El curso no existe o no está publicado"
    assert db.query(Pago).count() == 0
    assert db.query(Inscripcion).filter(Inscripcion.id_usuario_inscrito == pedro.id_usuario).count() == 0


@pytest.mark.parametrize("cuerpo, mensaje", [
    ({"metodo_pago": "TARJETA", "numero_tarjeta": "123", "titular": "Pedro Gil"},
     "El número de tarjeta debe tener 16 dígitos"),
    ({"metodo_pago": "TARJETA", "numero_tarjeta": "4242 4242 4242 4242", "titular": " "},
     "Debe escribir el nombre del titular"),
    ({"metodo_pago": "PSE", "banco": "", "tipo_persona": "NATURAL"}, "Debe seleccionar un banco"),
    ({"metodo_pago": "PSE", "banco": "BANCOLOMBIA", "tipo_persona": "EXTRATERRESTRE"},
     "El tipo de persona debe ser NATURAL o JURIDICA"),
    ({"metodo_pago": "BITCOIN"}, "Medio de pago no soportado: BITCOIN"),
], ids=["tarjeta_corta", "sin_titular", "pse_sin_banco", "pse_tipo_persona", "medio_no_soportado"])
def test_datos_de_pago_invalidos_por_la_api_no_dejan_rastro(cliente, db, escenario, cuerpo, mensaje):
    """HU-09 (ajuste E2): datos del medio de pago inválidos -> 400 con su mensaje; no queda pago ni inscripción."""
    pedro = _estudiante2(db)
    r = cliente.post(f"/checkout/cursos/{escenario['curso'].id_curso}", headers=token_de(pedro), json=cuerpo)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == mensaje
    assert db.query(Pago).count() == 0
    assert db.query(Inscripcion).filter(Inscripcion.id_usuario_inscrito == pedro.id_usuario).count() == 0
