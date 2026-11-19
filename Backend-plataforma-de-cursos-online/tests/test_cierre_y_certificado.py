"""
Pruebas del Observer (cierre automático, HU-16) y del Template Method (certificado, HU-13).
"""

from datetime import date

import pytest

from conftest import token_de
from src.entities.Evaluacion import Evaluacion
from src.entities.Leccion import Leccion
from src.entities.certificado import Certificado
from src.entities.registro_cierre import RegistroCierre
from src.patrones.certificado_generador import (
    DatosCertificado,
    GeneradorCertificado,
    GeneradorCertificadoPDF,
    GeneradorCertificadoTexto,
)
from src.patrones.cierre_academico import EventoCierre, ObservadorCierre, PublicadorCierre
from src.services.cierre import calcular_promedio_ponderado


# ------------------------------ OBSERVER -----------------------------------
class ObservadorEspia(ObservadorCierre):
    def __init__(self):
        self.eventos = []

    def actualizar(self, evento):
        self.eventos.append(evento)


def test_el_publicador_avisa_a_todos_los_suscritos():
    publicador = PublicadorCierre()
    a, b = ObservadorEspia(), ObservadorEspia()
    publicador.suscribir(a)
    publicador.suscribir(b)
    evento = EventoCierre(id_inscripcion=None, id_estudiante=None, estado_final="APROBADA", promedio=4.5)
    publicador.notificar(evento)
    assert a.eventos == [evento] and b.eventos == [evento]


def test_dip_el_observador_de_certificados_usa_la_emision_inyectada():
    """DIP: ObservadorCertificado no importa el servicio concreto; recibe la función de emisión.
    Con un doble se comprueba que emite solo cuando el estado final es APROBADA."""
    from src.patrones.cierre_academico import ObservadorCertificado

    llamadas = []
    observador = ObservadorCertificado(db=None, emitir=lambda db, **kw: llamadas.append(kw))
    observador.actualizar(EventoCierre(None, None, "REPROBADA", 2.0))
    assert llamadas == []
    observador.actualizar(EventoCierre("insc-1", "est-1", "APROBADA", 4.5))
    assert llamadas == [{"id_inscripcion": "insc-1", "promedio": 4.5, "id_usuario_creacion": "est-1", "guardar": False}]


def test_un_observador_desuscrito_ya_no_se_entera():
    publicador = PublicadorCierre()
    a = ObservadorEspia()
    publicador.suscribir(a)
    publicador.desuscribir(a)
    publicador.notificar(EventoCierre(None, None, "REPROBADA", 2.0))
    assert a.eventos == []


def test_promedio_ponderado():
    assert calcular_promedio_ponderado([(4.0, 60), (5.0, 40)]) == 4.4
    assert calcular_promedio_ponderado([(3.0, 50), (4.0, 50)]) == 3.5


def _preguntas(cliente, escenario, id_evaluacion):
    r = cliente.post(
        f"/evaluaciones/{id_evaluacion}/preguntas",
        headers=token_de(escenario["docente"]),
        json={"tipo": "VERDADERO_FALSO", "enunciado": "El contraste ayuda.", "respuesta_correcta": "Verdadero"},
    )
    return r.json()["id_pregunta"]


def _presentar(cliente, escenario, id_evaluacion, id_pregunta, respuesta):
    return cliente.post(
        f"/evaluaciones/{id_evaluacion}/presentar",
        headers=token_de(escenario["estudiante"]),
        json={"respuestas": {id_pregunta: respuesta}},
    ).json()


def test_aprobar_la_ultima_evaluacion_cierra_y_emite_certificado(cliente, db, escenario):
    ev = escenario["evaluacion"].id_evaluacion
    resultado = _presentar(cliente, escenario, ev, _preguntas(cliente, escenario, ev), "Verdadero")

    assert resultado["estado_curso"] == "APROBADA"
    assert resultado["promedio_curso"] == 5.0
    db.expire_all()
    certificado = db.query(Certificado).filter_by(id_inscripcion=escenario["inscripcion"].id_inscripcion).first()
    assert certificado.codigo_verificacion.startswith("CERT-")
    assert db.query(RegistroCierre).count() == 1  # el observador de auditoría también reaccionó

    # HU-13: ya puede descargar el PDF
    pdf = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}/certificado", headers=token_de(escenario["estudiante"]))
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")


def test_reprobar_cierra_sin_certificado_pero_con_auditoria(cliente, db, escenario):
    # La evaluación pide 2.0 para pasar; con 1 de 2 buenas saca 2.5: pasa la evaluación
    # pero el promedio del curso (2.5) no llega a 3.5 -> REPROBADA
    escenario["evaluacion"].nota_minima = 2.0
    db.commit()
    ev = escenario["evaluacion"].id_evaluacion
    p1 = _preguntas(cliente, escenario, ev)
    p2 = _preguntas(cliente, escenario, ev)
    resultado = cliente.post(
        f"/evaluaciones/{ev}/presentar",
        headers=token_de(escenario["estudiante"]),
        json={"respuestas": {p1: "Verdadero", p2: "Falso"}},
    ).json()

    assert resultado["nota"] == 2.5 and resultado["aprobada"] is True
    assert resultado["estado_curso"] == "REPROBADA"
    db.expire_all()
    assert db.query(Certificado).count() == 0
    assert db.query(RegistroCierre).first().estado_final == "REPROBADA"
    r = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}/certificado", headers=token_de(escenario["estudiante"]))
    assert r.status_code == 403


def test_si_faltan_evaluaciones_no_se_cierra(cliente, db, escenario):
    leccion2 = Leccion(id_curso=escenario["curso"].id_curso, titulo_leccion="Prototipado", orden=2,
                       duracion_horas=1, id_usuario_creacion=escenario["docente"].id_usuario)
    db.add(leccion2)
    db.commit()
    db.add(Evaluacion(id_leccion=leccion2.id_leccion, nombre_evaluacion="Proyecto final", porcentaje=50,
                      nota_minima=3.0, id_usuario_creacion=escenario["docente"].id_usuario))
    db.commit()

    ev = escenario["evaluacion"].id_evaluacion
    resultado = _presentar(cliente, escenario, ev, _preguntas(cliente, escenario, ev), "Verdadero")
    assert resultado["estado_curso"] is None  # todavía le falta el proyecto final


def test_perder_una_evaluacion_no_cierra_el_curso_y_puede_reintentar(cliente, db, escenario):
    """RN-04 + HU-15 esc. 2: si pierde una evaluación sigue ACTIVO y puede volver a intentarlo."""
    ev = escenario["evaluacion"].id_evaluacion
    pregunta = _preguntas(cliente, escenario, ev)
    primero = _presentar(cliente, escenario, ev, pregunta, "Falso")
    assert primero["aprobada"] is False and primero["estado_curso"] is None

    aula = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["estudiante"])).json()
    assert aula["estado_inscripcion"] == "ACTIVA"
    assert aula["mensaje_cierre"] == "Debes presentar todas las evaluaciones antes del cierre académico"  # HU-16 esc. 3

    segundo = _presentar(cliente, escenario, ev, pregunta, "Verdadero")
    assert segundo["numero_intento"] == 2 and segundo["estado_curso"] == "APROBADA"


def test_sin_aprobar_no_hay_certificado(cliente, escenario):
    r = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}/certificado", headers=token_de(escenario["estudiante"]))
    assert r.status_code == 403
    assert "una vez el curso sea aprobado" in r.json()["detail"]


def test_el_administrador_no_puede_emitir_certificados_a_mano(cliente, escenario):
    """RN-04 / RF-16: el único camino de emisión es el cierre automático; no existe POST /certificados."""
    r = cliente.post("/certificados", headers=token_de(escenario["admin"]),
                     json={"id_inscripcion": str(escenario["inscripcion"].id_inscripcion)})
    assert r.status_code == 405


# ------------------------------ TEMPLATE METHOD ----------------------------
DATOS = DatosCertificado(
    institucion="Campus Digital", estudiante="Lucía Martínez", documento="CC 300",
    curso="Diseño de interfaces con Figma", horas=12, docente="Ana Torres",
    fecha=date(2026, 9, 28), promedio=4.5, codigo="CERT-2026-ABC123",
)


def test_el_generador_arma_el_certificado_en_texto_con_los_pasos_en_orden():
    texto = GeneradorCertificadoTexto().generar(DATOS)
    lineas = texto.splitlines()
    assert lineas[0] == "CAMPUS DIGITAL"  # el orden lo fija generar() en la clase base
    assert "Lucía Martínez" in lineas[2] and "Diseño de interfaces con Figma" in lineas[3]
    assert "4.5" in lineas[4] and "CERT-2026-ABC123" in lineas[-1]


@pytest.mark.parametrize("generador", [GeneradorCertificadoPDF(), GeneradorCertificadoTexto()], ids=["PDF", "Texto"])
def test_sustitucion_lsp_cualquier_generador_entrega_el_certificado(generador):
    """LSP: el servicio solo conoce GeneradorCertificado; cualquier generador concreto sirve."""
    assert isinstance(generador, GeneradorCertificado)
    assert type(generador).generar is GeneradorCertificado.generar  # ninguna clase hija redefine el orden
    producto = generador.generar(DATOS)
    assert producto  # siempre entrega un documento no vacío
    if isinstance(producto, bytes):
        assert producto.startswith(b"%PDF")


def test_aprobar_la_evaluacion_completa_su_leccion(cliente, db, escenario):
    """Si la aprobó, la estudió: la lección queda completada y el avance sube (HU-12)."""
    ev = escenario["evaluacion"].id_evaluacion
    _presentar(cliente, escenario, ev, _preguntas(cliente, escenario, ev), "Verdadero")
    aula = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["estudiante"])).json()
    assert aula["porcentaje_avance"] == 100 and aula["lecciones"][0]["completada"] is True


def test_con_lecciones_pendientes_no_se_cierra_y_cierra_al_completarlas(cliente, db, escenario):
    """HU-16 esc. 3: 'evaluaciones o lecciones pendientes'. Al completar la última lección se cierra."""
    leccion2 = Leccion(id_curso=escenario["curso"].id_curso, titulo_leccion="Repaso final", orden=2,
                       duracion_horas=1, id_usuario_creacion=escenario["docente"].id_usuario)
    db.add(leccion2)
    db.commit()

    ev = escenario["evaluacion"].id_evaluacion
    resultado = _presentar(cliente, escenario, ev, _preguntas(cliente, escenario, ev), "Verdadero")
    assert resultado["aprobada"] is True and resultado["estado_curso"] is None  # le falta la lección 2

    aula = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["estudiante"])).json()
    assert aula["lecciones_pendientes"] == 1
    assert aula["mensaje_cierre"] == "Debes presentar todas las evaluaciones antes del cierre académico"

    r = cliente.post(f"/mis-cursos/lecciones/{leccion2.id_leccion}/completar", headers=token_de(escenario["estudiante"])).json()
    assert r["porcentaje_avance"] == 100 and r["estado_curso"] == "APROBADA"
    db.expire_all()
    assert db.query(Certificado).count() == 1  # el Observer emitió el certificado
