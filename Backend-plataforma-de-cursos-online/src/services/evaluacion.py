"""
Evaluaciones de las lecciones (HU-14). Las preguntas se crean aparte con la Factory (services/pregunta.py).

Reglas:
- Una evaluación por lección y siempre colgada de una lección (RN-03).
- Nota mínima entre 0 y 5 (HU-14 esc. 3).
- Los porcentajes de las evaluaciones de un curso suman máximo 100.
- Solo se puede editar mientras ningún estudiante la haya presentado (HU-14 esc. 2).
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.Evaluacion import NOTA_MINIMA_POR_DEFECTO, Evaluacion
from src.entities.Leccion import Leccion
from src.entities.calificacion import Calificacion
from src.entities.intento_evaluacion import IntentoEvaluacion
from src.entities.pregunta import Pregunta
from src.entities.usuario import Usuario
from src.patrones.factory_preguntas import MENSAJE_CLAVE_INVALIDA
from src.services import leccion as leccion_services
from src.services import historial as servicio_historial
from src.services.permisos import curso_de_evaluacion, curso_de_leccion, es_admin, exigir_gestion_curso

MENSAJE_YA_RESPONDIDA = "La evaluación ya fue presentada por estudiantes y no se puede modificar"


def _validar_nota_minima(nota_minima: float) -> None:
    if nota_minima is None or not (0 <= nota_minima <= 5):
        raise ValueError(MENSAJE_CLAVE_INVALIDA)  # HU-14 esc. 3


def _validar_suma_porcentajes(db: Session, id_curso: UUID, porcentaje: float, excepto: Optional[UUID] = None) -> None:
    consulta = (
        db.query(Evaluacion)
        .join(Leccion, Leccion.id_leccion == Evaluacion.id_leccion)
        .filter(Leccion.id_curso == id_curso)
    )
    if excepto:
        consulta = consulta.filter(Evaluacion.id_evaluacion != excepto)
    usado = sum(e.porcentaje for e in consulta.all())
    if usado + porcentaje > 100:
        raise ValueError(f"Los porcentajes de las evaluaciones del curso no pueden pasar de 100 % (ya hay {usado:g} %)")


def ya_fue_presentada(db: Session, id_evaluacion: UUID) -> bool:
    return bool(
        db.query(Calificacion).filter(Calificacion.id_evaluacion == id_evaluacion).first()
        or db.query(IntentoEvaluacion).filter(IntentoEvaluacion.id_evaluacion == id_evaluacion).first()
    )


def crear(
    db: Session,
    usuario: Usuario,
    id_leccion: UUID,
    nombre_evaluacion: str,
    porcentaje: float,
    nota_minima: float = NOTA_MINIMA_POR_DEFECTO,
) -> Evaluacion:
    leccion = leccion_services.obtener_por_id(db, id_leccion)
    if not leccion:
        raise ValueError("La lección no existe")  # RN-03
    exigir_gestion_curso(usuario, curso_de_leccion(db, leccion))
    if db.query(Evaluacion).filter(Evaluacion.id_leccion == id_leccion).first():
        raise ValueError("Esta lección ya tiene una evaluación")
    _validar_nota_minima(nota_minima)
    _validar_suma_porcentajes(db, leccion.id_curso, porcentaje)

    evaluacion = Evaluacion(
        id_leccion=id_leccion,
        nombre_evaluacion=nombre_evaluacion.strip(),
        porcentaje=porcentaje,
        nota_minima=nota_minima,
        id_usuario_creacion=usuario.id_usuario,
    )
    db.add(evaluacion)
    db.commit()
    db.refresh(evaluacion)
    return evaluacion


def obtener_por_id(db: Session, id_evaluacion: UUID) -> Optional[Evaluacion]:
    return db.query(Evaluacion).filter(Evaluacion.id_evaluacion == id_evaluacion).first()


def obtener_para_usuario(db: Session, usuario: Usuario) -> List[Evaluacion]:
    """El Docente solo ve las evaluaciones de sus cursos."""
    consulta = db.query(Evaluacion)
    if not es_admin(usuario):
        ids_lecciones = [l.id_leccion for l in leccion_services.obtener_para_usuario(db, usuario)]
        consulta = consulta.filter(Evaluacion.id_leccion.in_(ids_lecciones))
    return consulta.all()


def evaluacion_editable(db: Session, id_evaluacion: UUID, usuario: Usuario) -> Optional[Evaluacion]:
    """La evaluación, si el usuario puede tocarla y nadie la ha presentado (HU-14 esc. 2)."""
    evaluacion = obtener_por_id(db, id_evaluacion)
    if not evaluacion:
        return None
    exigir_gestion_curso(usuario, curso_de_evaluacion(db, evaluacion))
    if ya_fue_presentada(db, id_evaluacion):
        raise ValueError(MENSAJE_YA_RESPONDIDA)
    return evaluacion


def actualizar(db: Session, id_evaluacion: UUID, usuario: Usuario, **cambios) -> Optional[Evaluacion]:
    evaluacion = evaluacion_editable(db, id_evaluacion, usuario)
    if not evaluacion:
        return None
    if "nota_minima" in cambios:
        _validar_nota_minima(cambios["nota_minima"])
    if cambios.get("porcentaje") is not None:
        leccion = leccion_services.obtener_por_id(db, evaluacion.id_leccion)
        _validar_suma_porcentajes(db, leccion.id_curso, cambios["porcentaje"], excepto=id_evaluacion)

    detalle, cambio = servicio_historial.describir_cambios(evaluacion, cambios)  # RF-07
    for campo, valor in cambios.items():
        if valor is not None:
            setattr(evaluacion, campo, valor.strip() if isinstance(valor, str) else valor)
    if cambio:
        servicio_historial.registrar(db, id_usuario=usuario.id_usuario, entidad="EVALUACION", id_registro=evaluacion.id_evaluacion,
                                     nombre_registro=evaluacion.nombre_evaluacion, accion=servicio_historial.ACTUALIZAR, detalle=detalle)
    evaluacion.id_usuario_edita = usuario.id_usuario
    db.commit()
    db.refresh(evaluacion)
    return evaluacion


def eliminar(db: Session, id_evaluacion: UUID, usuario: Usuario) -> bool:
    evaluacion = evaluacion_editable(db, id_evaluacion, usuario)
    if not evaluacion:
        return False
    n_preguntas = db.query(Pregunta).filter(Pregunta.id_evaluacion == id_evaluacion).count()
    servicio_historial.registrar(db, id_usuario=usuario.id_usuario, entidad="EVALUACION", id_registro=evaluacion.id_evaluacion,
                                 nombre_registro=evaluacion.nombre_evaluacion, accion=servicio_historial.ELIMINAR,
                                 detalle=f"Evaluación eliminada: {evaluacion.nombre_evaluacion} (con {n_preguntas} pregunta(s))")  # RF-07
    db.query(Pregunta).filter(Pregunta.id_evaluacion == id_evaluacion).delete()  # sus preguntas se van con ella
    db.delete(evaluacion)
    db.commit()
    return True
