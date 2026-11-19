"""
Lecciones de un curso (HU-11). Cada lección tiene un número de orden único dentro de su curso.
Solo el profesor del curso o el Admin pueden crearlas, cambiarlas o borrarlas (RN-02).
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.Evaluacion import Evaluacion
from src.entities.Leccion import Leccion
from src.entities.Material import Material
from src.entities.progreso_leccion import ProgresoLeccion
from src.entities.usuario import Usuario
from src.services import curso as curso_services
from src.services import historial as servicio_historial
from src.services.permisos import curso_de_leccion, es_admin, exigir_gestion_curso

MENSAJE_TITULO_Y_ORDEN = "Debe asignar un título y un número de orden a la lección"  # HU-11 esc. 4
MENSAJE_ORDEN_REPETIDO = "Ya existe una lección con este orden en el curso"


def crear(
    db: Session,
    usuario: Usuario,
    id_curso: UUID,
    titulo_leccion: Optional[str],
    orden: Optional[int],
    duracion_horas: int = 1,
    descripcion_leccion: Optional[str] = None,
) -> Leccion:
    curso = curso_services.obtener_por_id(db, id_curso)
    if not curso:
        raise ValueError("El curso no existe")
    exigir_gestion_curso(usuario, curso)

    if not (titulo_leccion or "").strip() or orden is None or orden < 1:
        raise ValueError(MENSAJE_TITULO_Y_ORDEN)
    if obtener_por_orden_y_curso(db, orden, id_curso):
        raise ValueError(MENSAJE_ORDEN_REPETIDO)

    leccion = Leccion(
        id_curso=id_curso,
        titulo_leccion=titulo_leccion.strip(),
        descripcion_leccion=descripcion_leccion,
        orden=orden,
        duracion_horas=duracion_horas,
        id_usuario_creacion=usuario.id_usuario,
    )
    db.add(leccion)
    db.commit()
    db.refresh(leccion)
    return leccion


def obtener_por_id(db: Session, id_leccion: UUID) -> Optional[Leccion]:
    return db.query(Leccion).filter(Leccion.id_leccion == id_leccion).first()


def obtener_para_usuario(db: Session, usuario: Usuario, id_curso: Optional[UUID] = None) -> List[Leccion]:
    """Lecciones en orden. El Docente solo ve las de sus cursos."""
    ids_cursos = [c.id_curso for c in curso_services.obtener_para_usuario(db, usuario, 0, 10_000)]
    consulta = db.query(Leccion)
    if not es_admin(usuario):
        consulta = consulta.filter(Leccion.id_curso.in_(ids_cursos))
    if id_curso:
        consulta = consulta.filter(Leccion.id_curso == id_curso)
    return consulta.order_by(Leccion.id_curso, Leccion.orden).all()


def obtener_por_orden_y_curso(db: Session, orden: int, id_curso: UUID) -> Optional[Leccion]:
    return db.query(Leccion).filter(Leccion.orden == orden, Leccion.id_curso == id_curso).first()


def actualizar(db: Session, id_leccion: UUID, usuario: Usuario, **cambios) -> Optional[Leccion]:
    leccion = obtener_por_id(db, id_leccion)
    if not leccion:
        return None
    exigir_gestion_curso(usuario, curso_de_leccion(db, leccion))

    if "titulo_leccion" in cambios and not (cambios["titulo_leccion"] or "").strip():
        raise ValueError(MENSAJE_TITULO_Y_ORDEN)
    if "orden" in cambios:
        nuevo_orden = cambios["orden"]
        if nuevo_orden is None or nuevo_orden < 1:
            raise ValueError(MENSAJE_TITULO_Y_ORDEN)
        otra = obtener_por_orden_y_curso(db, nuevo_orden, leccion.id_curso)
        if otra and otra.id_leccion != leccion.id_leccion:
            raise ValueError(MENSAJE_ORDEN_REPETIDO)

    detalle, cambio = servicio_historial.describir_cambios(leccion, cambios)  # RF-07
    for campo, valor in cambios.items():
        if valor is not None:
            setattr(leccion, campo, valor.strip() if isinstance(valor, str) else valor)
    if cambio:
        servicio_historial.registrar(db, id_usuario=usuario.id_usuario, entidad="LECCION", id_registro=leccion.id_leccion,
                                     nombre_registro=leccion.titulo_leccion, accion=servicio_historial.ACTUALIZAR, detalle=detalle)
    leccion.id_usuario_edita = usuario.id_usuario
    db.commit()
    db.refresh(leccion)
    return leccion


def eliminar(db: Session, id_leccion: UUID, usuario: Usuario) -> bool:
    leccion = obtener_por_id(db, id_leccion)
    if not leccion:
        return False
    curso = curso_de_leccion(db, leccion)
    exigir_gestion_curso(usuario, curso)
    # HU-05 esc. 3: un curso publicado no se puede quedar sin lecciones
    if curso_services.esta_publicado(curso) and db.query(Leccion).filter(Leccion.id_curso == curso.id_curso).count() == 1:
        raise ValueError("Un curso publicado debe tener al menos una lección; no puede eliminar la única que tiene")
    # RN-03: el material y la evaluación cuelgan de la lección; no se dejan huérfanos
    tiene_contenido = (
        db.query(Material).filter(Material.id_leccion == id_leccion).first()
        or db.query(Evaluacion).filter(Evaluacion.id_leccion == id_leccion).first()
        or db.query(ProgresoLeccion).filter(ProgresoLeccion.id_leccion == id_leccion).first()
    )
    if tiene_contenido:
        raise ValueError("La lección tiene materiales, evaluación o avance de estudiantes y no se puede eliminar")
    servicio_historial.registrar(db, id_usuario=usuario.id_usuario, entidad="LECCION", id_registro=leccion.id_leccion,
                                 nombre_registro=leccion.titulo_leccion, accion=servicio_historial.ELIMINAR,
                                 detalle=f"Lección eliminada: {leccion.orden}. {leccion.titulo_leccion} (curso {curso.nombre_curso})")  # RF-07
    db.delete(leccion)
    db.commit()
    return True
