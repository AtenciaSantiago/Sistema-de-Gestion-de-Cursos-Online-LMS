"""
Inscripciones (RF-10).

Entregable 2: el estado de la inscripción lo cambia el SISTEMA, no el administrador
(por eso se eliminó la HU-08 en el arreglo del E1):
- PENDIENTE -> ACTIVA: cuando la pasarela aprueba el pago (HU-09, services/checkout.py).
- ACTIVA -> APROBADA / REPROBADA: el cierre académico automático (HU-16, services/cierre.py).
Al Admin solo le quedan dos acciones manuales del RF-10: matricular a mano (queda ACTIVA)
y cancelar una inscripción PENDIENTE o ACTIVA. Nunca puede aprobar a nadie.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.Curso import Curso
from src.entities.certificado import Certificado
from src.entities.inscripcion import EstadoInscripcion, Inscripcion
from src.entities.registro_cierre import RegistroCierre
from src.entities.usuario import Usuario
from src.services.aula import porcentaje_avance
from src.services.curso import esta_publicado

ESTADOS_CANCELABLES = (EstadoInscripcion.PENDIENTE.value, EstadoInscripcion.ACTIVA.value)
# HU-17: estados de una inscripción ya cerrada, tal como los nombra el E1.
# (El cierre automático deja APROBADA o REPROBADA; FINALIZADA se conserva por compatibilidad.)
ESTADOS_CERRADOS = (
    EstadoInscripcion.APROBADA.value,
    EstadoInscripcion.REPROBADA.value,
    EstadoInscripcion.FINALIZADA.value,
)
MENSAJE_SIN_ESTUDIANTES = "Aún no hay estudiantes matriculados en este curso"  # HU-10 esc. 2


def obtener_por_id(db: Session, id_inscripcion: UUID) -> Optional[Inscripcion]:
    return db.query(Inscripcion).filter(Inscripcion.id_inscripcion == id_inscripcion).first()


def obtener_por_usuario_y_curso(db: Session, id_usuario: UUID, id_curso: UUID) -> Optional[Inscripcion]:
    return (
        db.query(Inscripcion)
        .filter(Inscripcion.id_usuario_inscrito == id_usuario, Inscripcion.id_curso == id_curso)
        .first()
    )


def obtener_todos(db: Session, estado: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Inscripcion]:
    """Listado del Admin. Con estado=APROBADA, REPROBADA... sirve de auditoría de cierres (HU-17)."""
    consulta = db.query(Inscripcion)
    if estado:
        estados_validos = [e.value for e in EstadoInscripcion]
        if estado.strip().upper() not in estados_validos:
            raise ValueError(f"Estado no válido. Use uno de: {', '.join(estados_validos)}")
        consulta = consulta.filter(Inscripcion.estado_inscripcion == estado.strip().upper())
    return consulta.order_by(Inscripcion.fecha_creacion.desc()).offset(skip).limit(limit).all()


def matricular_manual(db: Session, admin: Usuario, id_curso: UUID, id_estudiante: UUID) -> Inscripcion:
    curso = db.query(Curso).filter(Curso.id_curso == id_curso).first()
    if not esta_publicado(curso):
        raise ValueError("El curso no existe o no está publicado")
    estudiante = db.query(Usuario).filter(Usuario.id_usuario == id_estudiante).first()
    if not estudiante or (estudiante.rol or "").upper() != "ESTUDIANTE" or not estudiante.activo:
        raise ValueError("Solo se pueden matricular usuarios activos con rol Estudiante")

    inscripcion = obtener_por_usuario_y_curso(db, id_estudiante, id_curso)
    if inscripcion and inscripcion.estado_inscripcion not in (
        EstadoInscripcion.PENDIENTE.value,
        EstadoInscripcion.CANCELADA.value,
    ):
        raise ValueError("El estudiante ya tiene una inscripción en este curso")
    if inscripcion:  # estaba PENDIENTE o CANCELADA: se reactiva la misma
        inscripcion.estado_inscripcion = EstadoInscripcion.ACTIVA.value
        inscripcion.id_usuario_edita = admin.id_usuario
    else:
        inscripcion = Inscripcion(
            id_curso=id_curso,
            id_usuario_inscrito=id_estudiante,
            estado_inscripcion=EstadoInscripcion.ACTIVA.value,
            id_usuario_creacion=admin.id_usuario,
        )
        db.add(inscripcion)
    db.commit()
    db.refresh(inscripcion)
    return inscripcion


def cancelar(db: Session, id_inscripcion: UUID, admin: Usuario) -> Optional[Inscripcion]:
    """RF-10: cancelar por solicitud o mora. Le quita el acceso al curso (RF-09)."""
    inscripcion = obtener_por_id(db, id_inscripcion)
    if not inscripcion:
        return None
    if inscripcion.estado_inscripcion not in ESTADOS_CANCELABLES:
        raise ValueError("Solo se puede cancelar una inscripción PENDIENTE o ACTIVA")
    inscripcion.estado_inscripcion = EstadoInscripcion.CANCELADA.value
    inscripcion.id_usuario_edita = admin.id_usuario
    db.commit()
    db.refresh(inscripcion)
    return inscripcion


def datos_de_cierre(db: Session, inscripcion: Inscripcion) -> dict:
    """Promedio y código de certificado de una inscripción ya cerrada (para la auditoría)."""
    registro = (
        db.query(RegistroCierre)
        .filter(RegistroCierre.id_inscripcion == inscripcion.id_inscripcion)
        .order_by(RegistroCierre.fecha.desc())
        .first()
    )
    certificado = db.query(Certificado).filter(Certificado.id_inscripcion == inscripcion.id_inscripcion).first()
    return {
        "promedio_final": registro.promedio if registro else None,
        "codigo_certificado": certificado.codigo_verificacion if certificado else None,
    }


def cierres(db: Session, estado: Optional[str] = None) -> List[Inscripcion]:
    """HU-17: solo las inscripciones cerradas; con filtro opcional (ej. solo APROBADA)."""
    estados = ESTADOS_CERRADOS
    if estado:
        if estado.strip().upper() not in ESTADOS_CERRADOS:
            raise ValueError("El filtro de cierres debe ser APROBADA, REPROBADA o FINALIZADA")
        estados = (estado.strip().upper(),)
    return (
        db.query(Inscripcion)
        .filter(Inscripcion.estado_inscripcion.in_(estados))
        .order_by(Inscripcion.fecha_edicion.desc(), Inscripcion.fecha_creacion.desc())
        .all()
    )


ESTADOS_REPORTE_HU10 = (EstadoInscripcion.ACTIVA.value, EstadoInscripcion.APROBADA.value, EstadoInscripcion.REPROBADA.value)


def estudiantes_del_curso(db: Session, id_curso: UUID) -> List[dict]:
    """
    HU-10 esc. 1: alumnos matriculados con correo, fecha de inscripción, avance y estado.
    Se listan los ACTIVOS y también los que ya cerraron el curso (APROBADA o REPROBADA),
    porque siguen siendo estudiantes del curso para el seguimiento académico; antes, cuando
    todos habían cerrado, el reporte salía vacío con el mensaje de «sin estudiantes» (bug).
    PENDIENTE (pago no aprobado) y CANCELADA no cuentan como matriculados.
    """
    inscripciones = (
        db.query(Inscripcion)
        .filter(Inscripcion.id_curso == id_curso, Inscripcion.estado_inscripcion.in_(ESTADOS_REPORTE_HU10))
        .order_by(Inscripcion.fecha_creacion)
        .all()
    )
    return [
        {
            "id_estudiante": i.id_usuario_inscrito,
            "nombre_estudiante": i.usuario_inscrito.nombre_usuario,
            "email": i.usuario_inscrito.email,
            "fecha_inscripcion": i.fecha_creacion,
            "porcentaje_avance": porcentaje_avance(db, i),
            "estado_inscripcion": i.estado_inscripcion,
        }
        for i in inscripciones
    ]
