"""
Presentar una evaluación y calificarla automáticamente (HU-15).

Flujo:
1. Si ya la aprobó, no puede volver a enviarla: ve su resultado en solo lectura (esc. 3).
   Si no, se verifica que tenga la inscripción ACTIVA en el curso.
2. Cada respuesta se compara con la clave usando la pregunta de la Factory
   (no importa si es opción múltiple o verdadero/falso: todas tienen es_correcta()).
3. Nota = (correctas / total) x 5   -> escala 0 a 5 que ya usaba el sistema.
4. Se guarda el intento (RF-13: queda cada intento) y la nota vigente en Calificacion.
5. Si la aprobó, su lección queda completada (sube el avance, HU-12).
6. Se revisa el cierre académico (HU-16). Intento, nota y cierre se guardan JUNTOS (un solo commit).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.Evaluacion import Evaluacion
from src.entities.Leccion import Leccion
from src.entities.calificacion import Calificacion
from src.entities.inscripcion import EstadoInscripcion, Inscripcion
from src.entities.intento_evaluacion import IntentoEvaluacion
from src.entities.progreso_leccion import ProgresoLeccion
from src.entities.pregunta import Pregunta as PreguntaEntidad
from src.services import cierre as servicio_cierre
from src.services import pregunta as servicio_preguntas

NOTA_MAXIMA = 5.0
MENSAJE_SIN_INSCRIPCION = "No cuenta con una inscripción activa para presentar esta evaluación"
MENSAJE_YA_APROBADA = "Esta evaluación ya fue aprobada; el resultado queda en modo de solo lectura"


@dataclass
class ResultadoEvaluacion:
    id_inscripcion: UUID
    id_evaluacion: UUID
    correctas: int
    total: int
    nota: float
    nota_minima: float
    aprobada: bool
    numero_intento: int
    # Si con esta evaluación se cerró el curso (HU-16), aquí viene el resultado final
    estado_curso: Optional[str] = None
    promedio_curso: Optional[float] = None


def calcular_nota(correctas: int, total: int) -> float:
    """Regla de tres: si todo está bien es 5.0; se redondea a 1 decimal como en el colegio."""
    if total == 0:
        return 0.0
    return round(correctas / total * NOTA_MAXIMA, 1)


def _evaluacion_e_inscripcion(
    db: Session, id_evaluacion: UUID, id_estudiante: UUID, solo_activa: bool = True
) -> Tuple[Evaluacion, Inscripcion]:
    evaluacion = db.query(Evaluacion).filter(Evaluacion.id_evaluacion == id_evaluacion).first()
    if not evaluacion:
        raise ValueError("La evaluación no existe")
    # La evaluación pertenece a una lección y la lección a un curso
    leccion = db.query(Leccion).filter(Leccion.id_leccion == evaluacion.id_leccion).first()
    inscripcion = (
        db.query(Inscripcion)
        .filter(Inscripcion.id_usuario_inscrito == id_estudiante, Inscripcion.id_curso == leccion.id_curso)
        .first()
    )
    if not inscripcion or (solo_activa and inscripcion.estado_inscripcion != EstadoInscripcion.ACTIVA.value):
        raise PermissionError(MENSAJE_SIN_INSCRIPCION)
    return evaluacion, inscripcion


def preguntas_para_presentar(db: Session, id_evaluacion: UUID, id_estudiante: UUID) -> List[PreguntaEntidad]:
    """Las preguntas (sin la clave) solo las ve quien tiene la inscripción ACTIVA."""
    _evaluacion_e_inscripcion(db, id_evaluacion, id_estudiante)
    return servicio_preguntas.listar_por_evaluacion(db, id_evaluacion)


def mi_resultado(db: Session, id_evaluacion: UUID, id_estudiante: UUID) -> Dict:
    """HU-15 esc. 3: el resultado anterior para mostrarlo en solo lectura."""
    evaluacion, inscripcion = _evaluacion_e_inscripcion(db, id_evaluacion, id_estudiante, solo_activa=False)
    calificacion = (
        db.query(Calificacion)
        .filter(Calificacion.id_inscripcion == inscripcion.id_inscripcion, Calificacion.id_evaluacion == id_evaluacion)
        .first()
    )
    intentos = (
        db.query(IntentoEvaluacion)
        .filter(IntentoEvaluacion.id_inscripcion == inscripcion.id_inscripcion, IntentoEvaluacion.id_evaluacion == id_evaluacion)
        .order_by(IntentoEvaluacion.numero_intento)
        .all()
    )
    aprobada = evaluacion.aprueba(calificacion.Nota if calificacion else None)
    return {
        "id_evaluacion": evaluacion.id_evaluacion,
        "nombre_evaluacion": evaluacion.nombre_evaluacion,
        "nota": calificacion.Nota if calificacion else None,
        "nota_minima": evaluacion.nota_para_aprobar,
        "aprobada": aprobada,
        # Puede enviar si su inscripción sigue ACTIVA y todavía no la aprobó
        "puede_presentar": inscripcion.estado_inscripcion == EstadoInscripcion.ACTIVA.value and not aprobada,
        "intentos": [
            {"numero_intento": i.numero_intento, "nota": i.nota, "correctas": i.correctas, "total": i.total, "fecha": i.fecha}
            for i in intentos
        ],
    }


def presentar(db: Session, id_evaluacion: UUID, id_estudiante: UUID, respuestas: Dict[str, str]) -> ResultadoEvaluacion:
    # Primero se busca sin exigir ACTIVA: si ya la aprobó (y el curso se cerró) se le dice eso, no "sin inscripción"
    evaluacion, inscripcion = _evaluacion_e_inscripcion(db, id_evaluacion, id_estudiante, solo_activa=False)
    nota_minima = evaluacion.nota_para_aprobar

    calificacion = (
        db.query(Calificacion)
        .filter(Calificacion.id_inscripcion == inscripcion.id_inscripcion, Calificacion.id_evaluacion == id_evaluacion)
        .first()
    )
    if calificacion and evaluacion.aprueba(calificacion.Nota):
        raise ValueError(MENSAJE_YA_APROBADA)  # HU-15 esc. 3
    if inscripcion.estado_inscripcion != EstadoInscripcion.ACTIVA.value:
        raise PermissionError(MENSAJE_SIN_INSCRIPCION)

    preguntas = servicio_preguntas.listar_por_evaluacion(db, id_evaluacion)
    if not preguntas:
        raise ValueError("La evaluación todavía no tiene preguntas")

    # Calificación automática usando las preguntas de la Factory (lo que no respondió cuenta como mala)
    correctas = 0
    for entidad in preguntas:
        pregunta = servicio_preguntas.a_objeto_de_dominio(entidad)
        if pregunta.es_correcta(respuestas.get(str(entidad.id_pregunta), "")):
            correctas += 1
    nota = calcular_nota(correctas, len(preguntas))

    # RF-13: queda registrado CADA intento
    numero_intento = (
        db.query(IntentoEvaluacion)
        .filter(IntentoEvaluacion.id_inscripcion == inscripcion.id_inscripcion, IntentoEvaluacion.id_evaluacion == id_evaluacion)
        .count()
        + 1
    )
    db.add(
        IntentoEvaluacion(
            id_inscripcion=inscripcion.id_inscripcion,
            id_evaluacion=id_evaluacion,
            numero_intento=numero_intento,
            correctas=correctas,
            total=len(preguntas),
            nota=nota,
        )
    )

    # La nota vigente (la del último intento) va en Calificacion
    if calificacion:
        calificacion.Nota = nota
        calificacion.id_usuario_edita = id_estudiante
    else:
        db.add(
            Calificacion(
                id_inscripcion=inscripcion.id_inscripcion,
                id_evaluacion=id_evaluacion,
                Nota=nota,
                id_usuario_creacion=id_estudiante,
            )
        )
    # Si aprobó la evaluación, su lección queda completada (HU-12): si la aprobó, la estudió
    if evaluacion.aprueba(nota):
        ya_completada = (
            db.query(ProgresoLeccion)
            .filter(ProgresoLeccion.id_inscripcion == inscripcion.id_inscripcion, ProgresoLeccion.id_leccion == evaluacion.id_leccion)
            .first()
        )
        if not ya_completada:
            db.add(ProgresoLeccion(id_inscripcion=inscripcion.id_inscripcion, id_leccion=evaluacion.id_leccion))

    db.flush()  # todavía no se guarda: primero se mira si con esto se cierra el curso

    # HU-16: si era la última evaluación del curso, el sistema cierra solo (patrón Observer)
    evento = servicio_cierre.evaluar_cierre(db, inscripcion)
    db.commit()  # intento + nota + cierre quedan guardados juntos (o nada, si algo falla)

    return ResultadoEvaluacion(
        id_inscripcion=inscripcion.id_inscripcion,
        id_evaluacion=id_evaluacion,
        correctas=correctas,
        total=len(preguntas),
        nota=nota,
        nota_minima=nota_minima,
        aprobada=evaluacion.aprueba(nota),
        numero_intento=numero_intento,
        estado_curso=evento.estado_final if evento else None,
        promedio_curso=evento.promedio if evento else None,
    )
