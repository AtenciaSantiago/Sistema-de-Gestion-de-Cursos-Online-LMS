"""
Cierre académico automático (HU-16).

Se revisa cada vez que el estudiante presenta una evaluación o marca una lección como completada:
1. Todas las evaluaciones del curso deben estar presentadas Y aprobadas con su nota mínima
   (RN-04), y todas las lecciones completadas (HU-16 esc. 3 habla de "evaluaciones o lecciones
   pendientes"). Si falta algo, el curso sigue ACTIVO y puede reintentar (HU-15 esc. 2).
   Mensaje de la HU-16 esc. 3: "Debes presentar todas las evaluaciones antes del cierre académico".
2. Calcula el promedio ponderado (cada nota pesa según su porcentaje).
3. Si el promedio es >= 3.5 (equivale al 70 %) -> APROBADA; si no -> REPROBADA.
4. Le avisa a los observadores (auditoría y certificado) con el patrón Observer.
"""

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.entities.Evaluacion import Evaluacion
from src.entities.Leccion import Leccion
from src.entities.calificacion import Calificacion
from src.entities.inscripcion import EstadoInscripcion, Inscripcion
from src.entities.progreso_leccion import ProgresoLeccion
from src.services import certificado as servicio_certificados
from src.patrones.cierre_academico import (
    APROBADA,
    REPROBADA,
    EventoCierre,
    ObservadorAuditoria,
    ObservadorCertificado,
    PublicadorCierre,
)

NOTA_MINIMA_CURSO = 3.5  # 70 % de 5.0
MENSAJE_CURSO_INCOMPLETO = "Debes presentar todas las evaluaciones antes del cierre académico"  # HU-16 esc. 3


def publicador_por_defecto(db: Session) -> PublicadorCierre:
    """Aquí se arma quiénes se enteran del cierre. Para agregar otro, se suscribe aquí.

    Es el único lugar que conoce el servicio concreto de certificados: se lo inyecta al
    observador (DIP), así el patrón no depende de ese módulo y se puede probar con un doble.
    """
    publicador = PublicadorCierre()
    publicador.suscribir(ObservadorAuditoria(db))
    publicador.suscribir(ObservadorCertificado(db, emitir=servicio_certificados.emitir))
    return publicador


def calcular_promedio_ponderado(notas_y_pesos) -> float:
    """notas_y_pesos = [(nota, porcentaje), ...]. Ej: (4.0, 60) y (5.0, 40) -> 4.4"""
    total_pesos = sum(peso for _, peso in notas_y_pesos)
    if total_pesos == 0:
        return 0.0
    return round(sum(nota * peso for nota, peso in notas_y_pesos) / total_pesos, 2)


def _evaluaciones_del_curso(db: Session, id_curso) -> List[Evaluacion]:
    return (
        db.query(Evaluacion)
        .join(Leccion, Leccion.id_leccion == Evaluacion.id_leccion)
        .filter(Leccion.id_curso == id_curso)
        .all()
    )


def _notas(db: Session, inscripcion: Inscripcion) -> Dict:
    return {
        c.id_evaluacion: c.Nota
        for c in db.query(Calificacion).filter(Calificacion.id_inscripcion == inscripcion.id_inscripcion)
    }


def evaluaciones_pendientes(db: Session, inscripcion: Inscripcion) -> int:
    """Cuántas evaluaciones le faltan por presentar o por aprobar (para mostrarlo en el aula)."""
    notas = _notas(db, inscripcion)
    return sum(
        1
        for e in _evaluaciones_del_curso(db, inscripcion.id_curso)
        if not e.aprueba(notas.get(e.id_evaluacion))
    )


def lecciones_pendientes(db: Session, inscripcion: Inscripcion) -> int:
    """Cuántas lecciones del curso le falta marcar como completadas."""
    total = db.query(Leccion).filter(Leccion.id_curso == inscripcion.id_curso).count()
    hechas = db.query(ProgresoLeccion).filter(ProgresoLeccion.id_inscripcion == inscripcion.id_inscripcion).count()
    return max(total - hechas, 0)


def evaluar_cierre(db: Session, inscripcion: Inscripcion, publicador: PublicadorCierre = None) -> Optional[EventoCierre]:
    """Devuelve el evento si se cerró el curso, o None si todavía no se puede cerrar."""
    if inscripcion.estado_inscripcion != EstadoInscripcion.ACTIVA.value:
        return None  # ya estaba cerrado

    evaluaciones = _evaluaciones_del_curso(db, inscripcion.id_curso)
    if not evaluaciones or evaluaciones_pendientes(db, inscripcion) > 0 or lecciones_pendientes(db, inscripcion) > 0:
        return None  # HU-16 esc. 3: le faltan evaluaciones o lecciones

    notas = _notas(db, inscripcion)

    promedio = calcular_promedio_ponderado([(notas[e.id_evaluacion], e.porcentaje) for e in evaluaciones])
    estado_final = APROBADA if promedio >= NOTA_MINIMA_CURSO else REPROBADA

    inscripcion.estado_inscripcion = estado_final
    db.flush()  # el estado queda listo para que los observadores lo vean

    evento = EventoCierre(
        id_inscripcion=inscripcion.id_inscripcion,
        id_estudiante=inscripcion.id_usuario_inscrito,
        estado_final=estado_final,
        promedio=promedio,
    )
    # OBSERVER: el cierre solo avisa; cada observador sabe qué hacer
    (publicador or publicador_por_defecto(db)).notificar(evento)
    db.commit()  # se guarda todo junto: estado, auditoría y certificado
    return evento
