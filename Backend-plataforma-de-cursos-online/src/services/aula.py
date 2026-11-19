"""
Aula virtual del estudiante (HU-12: consumo de contenido y progreso).

- mis_cursos: los cursos donde está inscrito, con su % de avance.
- contenido_curso: lecciones en orden, con materiales, evaluación y si ya la completó.
- marcar_completada: el botón "Marcar como completada".

Regla (HU-12 escenario 4): si la inscripción está PENDIENTE o CANCELADA no se
muestra el contenido. Después del cierre (APROBADA o REPROBADA) puede seguir viendo
su curso y su resultado, pero ya no marca avance ni presenta evaluaciones.
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.Curso import Curso
from src.entities.Evaluacion import Evaluacion
from src.entities.Leccion import Leccion
from src.entities.Material import Material
from src.entities.calificacion import Calificacion
from src.entities.inscripcion import EstadoInscripcion, Inscripcion
from src.entities.progreso_leccion import ProgresoLeccion
from src.services import certificado as servicio_certificados
from src.services import cierre as servicio_cierre

# Con estos estados el estudiante puede entrar al aula (después del cierre sigue viendo su curso)
ESTADOS_CON_ACCESO = (
    EstadoInscripcion.ACTIVA.value,
    EstadoInscripcion.APROBADA.value,
    EstadoInscripcion.REPROBADA.value,
)


MENSAJE_SIN_ACCESO = "No cuenta con una inscripción activa para visualizar este contenido"  # HU-12 esc. 4


def _inscripcion_con_acceso(db: Session, id_estudiante: UUID, id_curso: UUID, solo_activa: bool = False) -> Inscripcion:
    inscripcion = (
        db.query(Inscripcion)
        .filter(Inscripcion.id_usuario_inscrito == id_estudiante, Inscripcion.id_curso == id_curso)
        .first()
    )
    permitidos = (EstadoInscripcion.ACTIVA.value,) if solo_activa else ESTADOS_CON_ACCESO
    if not inscripcion or inscripcion.estado_inscripcion not in permitidos:
        raise PermissionError(MENSAJE_SIN_ACCESO)
    return inscripcion


def _estado_del_certificado(db: Session, inscripcion: Inscripcion) -> Dict:
    """HU-13: si el botón de certificado va habilitado y qué mensaje se muestra."""
    estado = inscripcion.estado_inscripcion
    if estado == EstadoInscripcion.APROBADA.value:
        return {"certificado_disponible": True, "mensaje_certificado": None}
    if estado == EstadoInscripcion.REPROBADA.value:
        return {"certificado_disponible": False, "mensaje_certificado": servicio_certificados.MENSAJE_NO_CUMPLE}
    return {"certificado_disponible": False, "mensaje_certificado": servicio_certificados.MENSAJE_NO_DISPONIBLE}


def _lecciones(db: Session, id_curso: UUID) -> List[Leccion]:
    return db.query(Leccion).filter(Leccion.id_curso == id_curso).order_by(Leccion.orden).all()


def porcentaje_avance(db: Session, inscripcion: Inscripcion) -> int:
    total = db.query(Leccion).filter(Leccion.id_curso == inscripcion.id_curso).count()
    if total == 0:
        return 0
    hechas = db.query(ProgresoLeccion).filter(ProgresoLeccion.id_inscripcion == inscripcion.id_inscripcion).count()
    return round(hechas / total * 100)


def mis_cursos(db: Session, id_estudiante: UUID) -> List[Dict]:
    inscripciones = db.query(Inscripcion).filter(Inscripcion.id_usuario_inscrito == id_estudiante).all()
    resultado = []
    for ins in inscripciones:
        curso = db.query(Curso).filter(Curso.id_curso == ins.id_curso).first()
        resultado.append(
            {
                "id_inscripcion": ins.id_inscripcion,
                "id_curso": curso.id_curso,
                "nombre_curso": curso.nombre_curso,
                "descripcion_curso": curso.descripcion_curso,
                "duracion_horas": curso.duracion_horas,
                "estado_inscripcion": str(ins.estado_inscripcion),
                "porcentaje_avance": porcentaje_avance(db, ins),
            }
        )
    return resultado


def contenido_curso(db: Session, id_estudiante: UUID, id_curso: UUID) -> Dict:
    inscripcion = _inscripcion_con_acceso(db, id_estudiante, id_curso)
    curso = db.query(Curso).filter(Curso.id_curso == id_curso).first()
    completadas = {
        p.id_leccion
        for p in db.query(ProgresoLeccion).filter(ProgresoLeccion.id_inscripcion == inscripcion.id_inscripcion)
    }

    lecciones = []
    for leccion in _lecciones(db, id_curso):
        materiales = db.query(Material).filter(Material.id_leccion == leccion.id_leccion).all()
        evaluacion = db.query(Evaluacion).filter(Evaluacion.id_leccion == leccion.id_leccion).first()
        info_evaluacion = None
        if evaluacion:
            calificacion = (
                db.query(Calificacion)
                .filter(
                    Calificacion.id_inscripcion == inscripcion.id_inscripcion,
                    Calificacion.id_evaluacion == evaluacion.id_evaluacion,
                )
                .first()
            )
            info_evaluacion = {
                "id_evaluacion": evaluacion.id_evaluacion,
                "nombre_evaluacion": evaluacion.nombre_evaluacion,
                "porcentaje": evaluacion.porcentaje,
                "nota_minima": evaluacion.nota_para_aprobar,
                "nota_obtenida": calificacion.Nota if calificacion else None,
                # HU-15 esc. 3: si ya la aprobó, el botón de presentar se deshabilita
                "aprobada": evaluacion.aprueba(calificacion.Nota if calificacion else None),
            }
        lecciones.append(
            {
                "id_leccion": leccion.id_leccion,
                "orden": leccion.orden,
                "titulo_leccion": leccion.titulo_leccion,
                "descripcion_leccion": leccion.descripcion_leccion,
                "duracion_horas": leccion.duracion_horas,
                "completada": leccion.id_leccion in completadas,
                "materiales": [
                    {
                        "id_material": m.id_material,
                        "titulo_material": m.titulo_material,
                        "tipo_material": m.tipo_material,
                        "URL_archivo": m.URL_archivo,
                    }
                    for m in materiales
                ],
                "evaluacion": info_evaluacion,
            }
        )

    pendientes = servicio_cierre.evaluaciones_pendientes(db, inscripcion)
    lecciones_sin_completar = servicio_cierre.lecciones_pendientes(db, inscripcion)
    activa = inscripcion.estado_inscripcion == EstadoInscripcion.ACTIVA.value
    return {
        "id_inscripcion": inscripcion.id_inscripcion,
        "id_curso": curso.id_curso,
        "nombre_curso": curso.nombre_curso,
        "estado_inscripcion": str(inscripcion.estado_inscripcion),
        "porcentaje_avance": porcentaje_avance(db, inscripcion),
        "evaluaciones_pendientes": pendientes,
        "lecciones_pendientes": lecciones_sin_completar,
        # HU-16 esc. 3: mientras falten evaluaciones o lecciones el curso sigue ACTIVO
        "mensaje_cierre": servicio_cierre.MENSAJE_CURSO_INCOMPLETO if activa and (pendientes or lecciones_sin_completar) else None,
        **_estado_del_certificado(db, inscripcion),
        "lecciones": lecciones,
    }


def marcar_completada(db: Session, id_estudiante: UUID, id_leccion: UUID) -> Tuple[int, Optional[str]]:
    """
    Marca la lección como vista. Devuelve el nuevo % de avance y, si con esta lección
    el curso quedó completo, el estado del cierre (HU-16: APROBADA o REPROBADA).
    """
    leccion = db.query(Leccion).filter(Leccion.id_leccion == id_leccion).first()
    if not leccion:
        raise ValueError("La lección no existe")
    # Solo con la inscripción ACTIVA: después del cierre el avance ya no cambia
    inscripcion = _inscripcion_con_acceso(db, id_estudiante, leccion.id_curso, solo_activa=True)

    ya_marcada = (
        db.query(ProgresoLeccion)
        .filter(ProgresoLeccion.id_inscripcion == inscripcion.id_inscripcion, ProgresoLeccion.id_leccion == id_leccion)
        .first()
    )
    evento = None
    if not ya_marcada:  # si ya estaba marcada no se duplica
        db.add(ProgresoLeccion(id_inscripcion=inscripcion.id_inscripcion, id_leccion=id_leccion))
        db.flush()
        # HU-16: si ya tenía todas las evaluaciones aprobadas, esta era la última lección pendiente
        evento = servicio_cierre.evaluar_cierre(db, inscripcion)
        db.commit()
    return porcentaje_avance(db, inscripcion), (evento.estado_final if evento else None)

