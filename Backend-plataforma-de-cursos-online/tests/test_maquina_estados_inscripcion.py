"""
Entregable 3 - Máquina de estados de la Inscripción (RF-10, HU-09, HU-12, HU-15, HU-16).

Estados: PENDIENTE, ACTIVA, CANCELADA, APROBADA, REPROBADA (enum EstadoInscripcion).
Eventos reales del código:
- pagar_curso        POST /checkout/cursos/{id}          (services/checkout.py)
- matricular_manual  POST /inscripciones (Admin)         (services/inscripcion.py)
- cancelar           PUT  /inscripciones/{id}/cancelar   (services/inscripcion.py)
- marcar_completada  POST /mis-cursos/lecciones/{id}/completar (services/aula.py)
- presentar          POST /evaluaciones/{id}/presentar   (services/presentacion_evaluacion.py)
- evaluar_cierre     lo disparan presentar y marcar_completada (services/cierre.py)

Hay una prueba por transición (CP-01 a CP-25). La transición bajo prueba siempre se
ejecuta por la API; el estado final se lee de la base de datos.
"""

import pytest

from conftest import crear_usuario, token_de
from src.app import app
from src.endpoints.checkout import obtener_pasarela
from src.entities.Leccion import Leccion
from src.entities.Pago import Pago
from src.entities.certificado import Certificado
from src.entities.inscripcion import EstadoInscripcion, Inscripcion
from src.entities.intento_evaluacion import IntentoEvaluacion
from src.entities.progreso_leccion import ProgresoLeccion
from src.entities.registro_cierre import RegistroCierre
from src.patrones.pagos import APROBADO, RECHAZADO, PasarelaPago, ResultadoPago
from src.services.aula import MENSAJE_SIN_ACCESO
from src.services.checkout import MENSAJE_YA_FINALIZADO, MENSAJE_YA_MATRICULADO
from src.services.presentacion_evaluacion import MENSAJE_SIN_INSCRIPCION

PENDIENTE = EstadoInscripcion.PENDIENTE.value
ACTIVA = EstadoInscripcion.ACTIVA.value
CANCELADA = EstadoInscripcion.CANCELADA.value
APROBADA = EstadoInscripcion.APROBADA.value
REPROBADA = EstadoInscripcion.REPROBADA.value

# Estos dos textos no son constantes en services/inscripcion.py (líneas 95 y 72): se copian tal cual
MENSAJE_NO_CANCELABLE = "Solo se puede cancelar una inscripción PENDIENTE o ACTIVA"
MENSAJE_YA_INSCRITO = "El estudiante ya tiene una inscripción en este curso"

TARJETA = {"metodo_pago": "TARJETA", "numero_tarjeta": "4242 4242 4242 4242", "titular": "Carlos Ruiz"}


class PasarelaFalsa(PasarelaPago):
    """Pasarela de mentiras: responde lo que la prueba le diga y anota cada cobro."""

    def __init__(self):
        self.estado = APROBADO
        self.llamadas = []

    def cobrar(self, monto, referencia, fuente):
        self.llamadas.append({"monto": monto, "referencia": referencia, "fuente": fuente})
        return ResultadoPago(self.estado, f"PAG-FALSO-{len(self.llamadas)}", "respuesta falsa")


@pytest.fixture()
def pasarela():
    """Sustituye la pasarela del checkout (igual que test_pagos.py) y la restaura al terminar."""
    falsa = PasarelaFalsa()
    app.dependency_overrides[obtener_pasarela] = lambda: falsa
    yield falsa
    app.dependency_overrides.clear()


@pytest.fixture()
def carlos(db, escenario):
    """Estudiante sin ninguna inscripción (estado inicial de la máquina)."""
    return crear_usuario(db, "Carlos Ruiz", "carlos@email.com", "400", "Estudiante")


# ------------------------------ Ayudas ------------------------------------
def _pagar(cliente, pasarela, estudiante, curso, estado):
    """Evento pagar_curso con la respuesta de la pasarela que se indique."""
    pasarela.estado = estado
    return cliente.post(f"/checkout/cursos/{curso.id_curso}", headers=token_de(estudiante), json=TARJETA)


def _matricular(cliente, escenario, estudiante):
    """Evento matricular_manual (Admin)."""
    return cliente.post(
        "/inscripciones",
        headers=token_de(escenario["admin"]),
        json={"id_curso": str(escenario["curso"].id_curso), "id_usuario_inscrito": str(estudiante.id_usuario)},
    )


def _cancelar(cliente, escenario, id_inscripcion):
    """Evento cancelar (Admin)."""
    return cliente.put(f"/inscripciones/{id_inscripcion}/cancelar", headers=token_de(escenario["admin"]))


def _pregunta(cliente, escenario):
    r = cliente.post(
        f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/preguntas",
        headers=token_de(escenario["docente"]),
        json={"tipo": "VERDADERO_FALSO", "enunciado": "El contraste ayuda.", "respuesta_correcta": "Verdadero"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id_pregunta"]


def _presentar(cliente, escenario, respuestas):
    """Evento presentar (dispara evaluar_cierre)."""
    return cliente.post(
        f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/presentar",
        headers=token_de(escenario["estudiante"]),
        json={"respuestas": respuestas},
    )


def _fijar_estado(db, inscripcion, estado):
    """
    PREPARACIÓN (no es la transición bajo prueba): deja la inscripción en el estado de
    partida escribiendo directo en la base. Así cada prueba parte de un estado exacto
    sin depender de otra transición.
    """
    inscripcion.estado_inscripcion = estado
    db.commit()
    return inscripcion.id_inscripcion


def _inscripciones_de(db, estudiante, curso):
    db.expire_all()  # lo que guardó la API en su propia sesión
    return (
        db.query(Inscripcion)
        .filter(Inscripcion.id_usuario_inscrito == estudiante.id_usuario, Inscripcion.id_curso == curso.id_curso)
        .all()
    )


def _estado_en_base(db, id_inscripcion):
    db.expire_all()
    return db.query(Inscripcion).filter(Inscripcion.id_inscripcion == id_inscripcion).one().estado_inscripcion


def _pagos_de(db, estudiante):
    db.expire_all()
    return sorted(p.estado_pago for p in db.query(Pago).filter(Pago.id_usuario == estudiante.id_usuario))


# =================== Transiciones válidas: desde el estado inicial ===================
def test_cp01_primer_pago_rechazado_crea_la_inscripcion_pendiente(cliente, db, escenario, carlos, pasarela):
    """CP-01 (inicial -> PENDIENTE) HU-09 esc. 2: pago RECHAZADO deja PENDIENTE y guarda el Pago RECHAZADO."""
    r = _pagar(cliente, pasarela, carlos, escenario["curso"], RECHAZADO)

    assert r.status_code == 200, r.text
    assert r.json()["aprobado"] is False and r.json()["estado_inscripcion"] == PENDIENTE
    inscripciones = _inscripciones_de(db, carlos, escenario["curso"])
    assert [i.estado_inscripcion for i in inscripciones] == [PENDIENTE]
    assert _pagos_de(db, carlos) == [RECHAZADO]


def test_cp02_primer_pago_aprobado_crea_la_inscripcion_activa(cliente, db, escenario, carlos, pasarela):
    """CP-02 (inicial -> ACTIVA) HU-09 esc. 1 / RN-01: pago APROBADO deja ACTIVA y guarda el Pago APROBADO."""
    r = _pagar(cliente, pasarela, carlos, escenario["curso"], APROBADO)

    assert r.status_code == 200, r.text
    assert r.json()["aprobado"] is True and r.json()["estado_inscripcion"] == ACTIVA
    inscripciones = _inscripciones_de(db, carlos, escenario["curso"])
    assert [i.estado_inscripcion for i in inscripciones] == [ACTIVA]
    assert _pagos_de(db, carlos) == [APROBADO]


def test_cp03_matricula_manual_crea_la_inscripcion_activa(cliente, db, escenario, carlos):
    """CP-03 (inicial -> ACTIVA) RF-10: el administrador matricula a mano y queda ACTIVA, sin pago."""
    r = _matricular(cliente, escenario, carlos)

    assert r.status_code == 201, r.text
    assert r.json()["estado_inscripcion"] == ACTIVA
    inscripciones = _inscripciones_de(db, carlos, escenario["curso"])
    assert [i.estado_inscripcion for i in inscripciones] == [ACTIVA]
    assert inscripciones[0].id_usuario_creacion == escenario["admin"].id_usuario
    assert _pagos_de(db, carlos) == []


# =================== Transiciones válidas: desde PENDIENTE ===================
def test_cp04_reintento_de_pago_aprobado_activa_la_misma_inscripcion(cliente, db, escenario, carlos, pasarela):
    """CP-04 (PENDIENTE -> ACTIVA) HU-09: tras un rechazo, el reintento APROBADO activa la MISMA inscripción."""
    primero = _pagar(cliente, pasarela, carlos, escenario["curso"], RECHAZADO).json()
    assert primero["estado_inscripcion"] == PENDIENTE

    segundo = _pagar(cliente, pasarela, carlos, escenario["curso"], APROBADO)

    assert segundo.status_code == 200, segundo.text
    assert segundo.json()["id_inscripcion"] == primero["id_inscripcion"]
    inscripciones = _inscripciones_de(db, carlos, escenario["curso"])
    assert len(inscripciones) == 1  # no se duplicó
    assert inscripciones[0].estado_inscripcion == ACTIVA
    assert _pagos_de(db, carlos) == [APROBADO, RECHAZADO]


def test_cp05_segundo_pago_rechazado_sigue_pendiente(cliente, db, escenario, carlos, pasarela):
    """CP-05 (PENDIENTE -> PENDIENTE) HU-09 esc. 2: otro rechazo no cambia el estado y quedan dos pagos RECHAZADOS."""
    _pagar(cliente, pasarela, carlos, escenario["curso"], RECHAZADO)

    r = _pagar(cliente, pasarela, carlos, escenario["curso"], RECHAZADO)

    assert r.status_code == 200, r.text
    assert r.json()["aprobado"] is False and r.json()["estado_inscripcion"] == PENDIENTE
    inscripciones = _inscripciones_de(db, carlos, escenario["curso"])
    assert [i.estado_inscripcion for i in inscripciones] == [PENDIENTE]
    assert _pagos_de(db, carlos) == [RECHAZADO, RECHAZADO]


def test_cp06_matricula_manual_reactiva_una_inscripcion_pendiente(cliente, db, escenario, carlos, pasarela):
    """CP-06 (PENDIENTE -> ACTIVA) RF-10: matricular a mano sobre una PENDIENTE reactiva la misma inscripción."""
    pendiente = _pagar(cliente, pasarela, carlos, escenario["curso"], RECHAZADO).json()["id_inscripcion"]

    r = _matricular(cliente, escenario, carlos)

    assert r.status_code == 201, r.text
    assert r.json()["id_inscripcion"] == pendiente
    inscripciones = _inscripciones_de(db, carlos, escenario["curso"])
    assert len(inscripciones) == 1
    assert inscripciones[0].estado_inscripcion == ACTIVA
    assert inscripciones[0].id_usuario_edita == escenario["admin"].id_usuario


def test_cp07_cancelar_una_inscripcion_pendiente(cliente, db, escenario):
    """CP-07 (PENDIENTE -> CANCELADA) RF-10: el administrador cancela una inscripción PENDIENTE."""
    id_inscripcion = _fijar_estado(db, escenario["inscripcion"], PENDIENTE)

    r = _cancelar(cliente, escenario, id_inscripcion)

    assert r.status_code == 200, r.text
    assert r.json()["estado_inscripcion"] == CANCELADA
    assert _estado_en_base(db, id_inscripcion) == CANCELADA


# =================== Transiciones válidas: desde ACTIVA ===================
def test_cp08_cancelar_una_inscripcion_activa_quita_el_acceso(cliente, db, escenario):
    """CP-08 (ACTIVA -> CANCELADA) RF-10 / HU-12 esc. 4: al cancelar, el estudiante ya no ve el contenido."""
    id_inscripcion = escenario["inscripcion"].id_inscripcion  # la del escenario ya está ACTIVA

    r = _cancelar(cliente, escenario, id_inscripcion)

    assert r.status_code == 200, r.text
    assert _estado_en_base(db, id_inscripcion) == CANCELADA
    aula = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["estudiante"]))
    assert aula.status_code == 403
    assert aula.json()["detail"] == MENSAJE_SIN_ACCESO


def test_cp12_cierre_automatico_aprueba_y_emite_certificado(cliente, db, escenario):
    """CP-12 (ACTIVA -> APROBADA) HU-16 esc. 1: todo aprobado y promedio >= 3.5; queda auditoría y certificado."""
    id_inscripcion = escenario["inscripcion"].id_inscripcion
    pregunta = _pregunta(cliente, escenario)

    r = _presentar(cliente, escenario, {pregunta: "Verdadero"})

    assert r.status_code == 200, r.text
    assert r.json()["estado_curso"] == APROBADA
    assert _estado_en_base(db, id_inscripcion) == APROBADA
    registros = db.query(RegistroCierre).filter(RegistroCierre.id_inscripcion == id_inscripcion).all()
    assert [(x.estado_final, x.promedio) for x in registros] == [(APROBADA, 5.0)]
    assert db.query(Certificado).filter(Certificado.id_inscripcion == id_inscripcion).count() == 1


def test_cp13_cierre_automatico_reprueba_sin_certificado(cliente, db, escenario):
    """CP-13 (ACTIVA -> REPROBADA) HU-16 esc. 2: aprueba la evaluación (mínima 2.0) pero el promedio 2.5 < 3.5."""
    id_inscripcion = escenario["inscripcion"].id_inscripcion
    escenario["evaluacion"].nota_minima = 2.0  # preparación: igual que test_cierre_y_certificado.py
    db.commit()
    p1, p2 = _pregunta(cliente, escenario), _pregunta(cliente, escenario)

    r = _presentar(cliente, escenario, {p1: "Verdadero", p2: "Falso"})

    assert r.status_code == 200, r.text
    assert r.json()["nota"] == 2.5 and r.json()["estado_curso"] == REPROBADA
    assert _estado_en_base(db, id_inscripcion) == REPROBADA
    registros = db.query(RegistroCierre).filter(RegistroCierre.id_inscripcion == id_inscripcion).all()
    assert [(x.estado_final, x.promedio) for x in registros] == [(REPROBADA, 2.5)]
    assert db.query(Certificado).count() == 0  # el certificado solo existe en APROBADA


@pytest.mark.parametrize("pendiente", ["evaluacion_pendiente", "leccion_pendiente"])
def test_cp14_con_pendientes_el_cierre_no_cambia_el_estado(cliente, db, escenario, pendiente):
    """CP-14 (ACTIVA -> ACTIVA) HU-16 esc. 3: si falta aprobar una evaluación o completar una lección, sigue ACTIVA."""
    id_inscripcion = escenario["inscripcion"].id_inscripcion
    pregunta = _pregunta(cliente, escenario)
    if pendiente == "leccion_pendiente":
        db.add(Leccion(id_curso=escenario["curso"].id_curso, titulo_leccion="Repaso final", orden=2,
                       duracion_horas=1, id_usuario_creacion=escenario["docente"].id_usuario))
        db.commit()
        respuesta = "Verdadero"  # aprueba la evaluación, pero le queda la lección 2
    else:
        respuesta = "Falso"  # pierde la evaluación: le queda pendiente

    r = _presentar(cliente, escenario, {pregunta: respuesta})

    assert r.status_code == 200, r.text
    assert r.json()["estado_curso"] is None
    assert _estado_en_base(db, id_inscripcion) == ACTIVA
    assert db.query(RegistroCierre).count() == 0
    assert db.query(Certificado).count() == 0


# =================== Transiciones válidas: desde CANCELADA ===================
def test_cp09_matricula_manual_reactiva_una_inscripcion_cancelada(cliente, db, escenario):
    """CP-09 (CANCELADA -> ACTIVA) RF-10: el administrador vuelve a matricular y se reactiva la misma inscripción."""
    id_inscripcion = _fijar_estado(db, escenario["inscripcion"], CANCELADA)

    r = _matricular(cliente, escenario, escenario["estudiante"])

    assert r.status_code == 201, r.text
    assert r.json()["id_inscripcion"] == str(id_inscripcion)
    inscripciones = _inscripciones_de(db, escenario["estudiante"], escenario["curso"])
    assert [i.estado_inscripcion for i in inscripciones] == [ACTIVA]


def test_cp10_pago_aprobado_reactiva_una_inscripcion_cancelada(cliente, db, escenario, pasarela):
    """CP-10 (CANCELADA -> ACTIVA) HU-09: el estudiante vuelve a pagar y, con pago APROBADO, queda ACTIVA."""
    id_inscripcion = _fijar_estado(db, escenario["inscripcion"], CANCELADA)

    r = _pagar(cliente, pasarela, escenario["estudiante"], escenario["curso"], APROBADO)

    assert r.status_code == 200, r.text
    assert r.json()["id_inscripcion"] == str(id_inscripcion)
    inscripciones = _inscripciones_de(db, escenario["estudiante"], escenario["curso"])
    assert [i.estado_inscripcion for i in inscripciones] == [ACTIVA]
    assert _pagos_de(db, escenario["estudiante"]) == [APROBADO]


def test_cp11_pago_rechazado_no_cambia_una_inscripcion_cancelada(cliente, db, escenario, pasarela):
    """CP-11 (CANCELADA -> CANCELADA) HU-09 esc. 2: con pago RECHAZADO sigue CANCELADA (queda el Pago RECHAZADO)."""
    id_inscripcion = _fijar_estado(db, escenario["inscripcion"], CANCELADA)

    r = _pagar(cliente, pasarela, escenario["estudiante"], escenario["curso"], RECHAZADO)

    assert r.status_code == 200, r.text
    assert r.json()["aprobado"] is False and r.json()["estado_inscripcion"] == CANCELADA
    assert _estado_en_base(db, id_inscripcion) == CANCELADA
    assert _pagos_de(db, escenario["estudiante"]) == [RECHAZADO]


# =================== Transiciones que el sistema debe RECHAZAR ===================
def _cancelar_debe_rechazarse(cliente, db, escenario, estado):
    id_inscripcion = _fijar_estado(db, escenario["inscripcion"], estado)
    r = _cancelar(cliente, escenario, id_inscripcion)
    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_NO_CANCELABLE
    assert _estado_en_base(db, id_inscripcion) == estado  # no cambió


def test_cp15_no_se_cancela_una_inscripcion_aprobada(cliente, db, escenario):
    """CP-15 (APROBADA -x-> CANCELADA) RF-10: el cierre académico no se deshace cancelando."""
    _cancelar_debe_rechazarse(cliente, db, escenario, APROBADA)


def test_cp16_no_se_cancela_una_inscripcion_reprobada(cliente, db, escenario):
    """CP-16 (REPROBADA -x-> CANCELADA) RF-10: una inscripción ya cerrada no se cancela."""
    _cancelar_debe_rechazarse(cliente, db, escenario, REPROBADA)


def test_cp17_no_se_cancela_dos_veces(cliente, db, escenario):
    """CP-17 (CANCELADA -x-> CANCELADA) RF-10: cancelar una inscripción ya CANCELADA se rechaza."""
    _cancelar_debe_rechazarse(cliente, db, escenario, CANCELADA)


def test_cp18_pagar_con_inscripcion_activa_se_rechaza_sin_cobrar(cliente, db, escenario, pasarela):
    """CP-18 (ACTIVA -x-> pagar_curso) HU-09 esc. 3: ya matriculado; no se cobra ni se crea ningún Pago."""
    id_inscripcion = escenario["inscripcion"].id_inscripcion

    r = _pagar(cliente, pasarela, escenario["estudiante"], escenario["curso"], APROBADO)

    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_YA_MATRICULADO
    assert _estado_en_base(db, id_inscripcion) == ACTIVA
    assert db.query(Pago).count() == 0
    assert pasarela.llamadas == []  # nunca se llamó a la pasarela


def _pagar_curso_cerrado_debe_rechazarse(cliente, db, escenario, pasarela, estado):
    id_inscripcion = _fijar_estado(db, escenario["inscripcion"], estado)
    r = _pagar(cliente, pasarela, escenario["estudiante"], escenario["curso"], APROBADO)
    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_YA_FINALIZADO
    assert _estado_en_base(db, id_inscripcion) == estado  # no se le borró el resultado
    assert db.query(Pago).count() == 0
    assert pasarela.llamadas == []


def test_cp19_pagar_con_inscripcion_aprobada_se_rechaza(cliente, db, escenario, pasarela):
    """CP-19 (APROBADA -x-> pagar_curso) HU-09: un curso ya aprobado no se vuelve a comprar."""
    _pagar_curso_cerrado_debe_rechazarse(cliente, db, escenario, pasarela, APROBADA)


def test_cp20_pagar_con_inscripcion_reprobada_se_rechaza(cliente, db, escenario, pasarela):
    """CP-20 (REPROBADA -x-> pagar_curso) HU-09: un curso ya reprobado tampoco se vuelve a comprar."""
    _pagar_curso_cerrado_debe_rechazarse(cliente, db, escenario, pasarela, REPROBADA)


def _matricular_debe_rechazarse(cliente, db, escenario, estado):
    id_inscripcion = _fijar_estado(db, escenario["inscripcion"], estado)
    r = _matricular(cliente, escenario, escenario["estudiante"])
    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_YA_INSCRITO
    inscripciones = _inscripciones_de(db, escenario["estudiante"], escenario["curso"])
    assert [(i.id_inscripcion, i.estado_inscripcion) for i in inscripciones] == [(id_inscripcion, estado)]


def test_cp21_matricular_a_quien_ya_esta_activo_se_rechaza(cliente, db, escenario):
    """CP-21 (ACTIVA -x-> matricular_manual) RF-10: no se duplica la inscripción de un estudiante ACTIVO."""
    _matricular_debe_rechazarse(cliente, db, escenario, ACTIVA)


def test_cp22_matricular_a_quien_ya_aprobo_se_rechaza(cliente, db, escenario):
    """CP-22 (APROBADA -x-> matricular_manual) RF-10: el administrador no reabre un curso APROBADO."""
    _matricular_debe_rechazarse(cliente, db, escenario, APROBADA)


def test_cp23_matricular_a_quien_ya_reprobo_se_rechaza(cliente, db, escenario):
    """CP-23 (REPROBADA -x-> matricular_manual) RF-10: el administrador no reabre un curso REPROBADO."""
    _matricular_debe_rechazarse(cliente, db, escenario, REPROBADA)


def test_cp24_despues_del_cierre_no_se_marca_avance(cliente, db, escenario):
    """CP-24 (APROBADA -x-> marcar_completada) HU-12 / HU-16: tras el cierre el avance ya no cambia."""
    id_inscripcion = escenario["inscripcion"].id_inscripcion
    cierre = _presentar(cliente, escenario, {_pregunta(cliente, escenario): "Verdadero"}).json()
    assert cierre["estado_curso"] == APROBADA  # el cierre real dejó la inscripción APROBADA
    # El docente agrega una lección después del cierre: es la que el estudiante intenta marcar
    nueva = Leccion(id_curso=escenario["curso"].id_curso, titulo_leccion="Lección extra", orden=2,
                    duracion_horas=1, id_usuario_creacion=escenario["docente"].id_usuario)
    db.add(nueva)
    db.commit()
    avance_antes = db.query(ProgresoLeccion).filter(ProgresoLeccion.id_inscripcion == id_inscripcion).count()

    r = cliente.post(f"/mis-cursos/lecciones/{nueva.id_leccion}/completar", headers=token_de(escenario["estudiante"]))

    assert r.status_code == 403
    assert r.json()["detail"] == MENSAJE_SIN_ACCESO
    db.expire_all()
    assert db.query(ProgresoLeccion).filter(ProgresoLeccion.id_inscripcion == id_inscripcion).count() == avance_antes == 1
    assert _estado_en_base(db, id_inscripcion) == APROBADA


def test_cp25_con_inscripcion_cancelada_no_se_presenta_la_evaluacion(cliente, db, escenario):
    """CP-25 (CANCELADA -x-> presentar) HU-15 / RF-09: sin inscripción ACTIVA no se califica ni se guarda intento."""
    pregunta = _pregunta(cliente, escenario)
    id_inscripcion = _fijar_estado(db, escenario["inscripcion"], CANCELADA)

    r = _presentar(cliente, escenario, {pregunta: "Verdadero"})

    assert r.status_code == 403
    assert r.json()["detail"] == MENSAJE_SIN_INSCRIPCION
    db.expire_all()
    assert db.query(IntentoEvaluacion).count() == 0
    assert _estado_en_base(db, id_inscripcion) == CANCELADA
