"""
Cursos: creación y edición (HU-04), publicación (HU-05) y catálogo (HU-06).

Reglas del Entregable 2:
- Todo curso nuevo nace en BORRADOR (HU-04 esc. 2).
- Solo el Administrador lo pasa a PUBLICADO o lo devuelve a BORRADOR (HU-05).
- Para publicar debe tener información completa, profesor asignado y al menos
  una lección (HU-05 esc. 3, RF-04).
- Pasar a BORRADOR no afecta a los estudiantes ya matriculados (HU-05 esc. 2):
  el aula revisa la inscripción, no el estado del curso.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.Curso import Curso
from src.entities.Leccion import Leccion
from src.entities.inscripcion import Inscripcion
from src.entities.usuario import Usuario
from src.schemas.curso_schema import ESTADOS_CURSO
from src.services import categoria as categoria_services
from src.services import historial as servicio_historial
from src.services.permisos import es_admin, exigir_gestion_curso

BORRADOR = "BORRADOR"
PUBLICADO = "PUBLICADO"

MENSAJE_NO_PUBLICABLE = "El curso debe tener información completa y al menos una lección para ser publicado"  # HU-05 esc. 3


def _validar_docente(db: Session, id_docente: Optional[UUID]) -> None:
    docente = db.query(Usuario).filter(Usuario.id_usuario == id_docente).first() if id_docente else None
    if not docente or (docente.rol or "").upper() != "DOCENTE" or not docente.activo:
        raise ValueError("Debe asignar un profesor (usuario activo con rol Docente)")


def _nombre_en_uso(db: Session, nombre: str, excepto: Optional[UUID] = None) -> bool:
    consulta = db.query(Curso).filter(Curso.nombre_curso == nombre.strip())
    if excepto:
        consulta = consulta.filter(Curso.id_curso != excepto)
    return consulta.first() is not None


def crear(
    db: Session,
    usuario: Usuario,
    id_categoria: UUID,
    nombre_curso: str,
    descripcion_curso: str,
    duracion_horas: int,
    precio: float = 0.0,
    id_docente: Optional[UUID] = None,
) -> Curso:
    if _nombre_en_uso(db, nombre_curso):
        raise ValueError("El curso ya existe")
    if not categoria_services.obtener_por_id(db, id_categoria):
        raise ValueError("La categoría no existe")

    # El docente que crea el curso queda como profesor; el admin debe escoger uno
    if not es_admin(usuario):
        id_docente = usuario.id_usuario
    _validar_docente(db, id_docente)

    curso = Curso(
        id_categoria=id_categoria,
        nombre_curso=nombre_curso.strip(),
        descripcion_curso=descripcion_curso.strip(),
        precio=precio,
        duracion_horas=duracion_horas,
        estado_curso=BORRADOR,  # HU-04 esc. 2
        id_docente=id_docente,
        id_usuario_creacion=usuario.id_usuario,
    )
    db.add(curso)
    db.commit()
    db.refresh(curso)
    return curso


def obtener_por_id(db: Session, id_curso: UUID) -> Optional[Curso]:
    return db.query(Curso).filter(Curso.id_curso == id_curso).first()


def obtener_todos(db: Session, skip: int = 0, limit: int = 100) -> List[Curso]:
    return db.query(Curso).order_by(Curso.nombre_curso).offset(skip).limit(limit).all()


def obtener_para_usuario(db: Session, usuario: Usuario, skip: int = 0, limit: int = 100) -> List[Curso]:
    """El Admin ve todos; el Docente solo sus cursos asignados (HU-07)."""
    if es_admin(usuario):
        return obtener_todos(db, skip, limit)
    return (
        db.query(Curso)
        .filter(Curso.id_docente == usuario.id_usuario)
        .order_by(Curso.nombre_curso)
        .offset(skip)
        .limit(limit)
        .all()
    )


def esta_publicado(curso: Optional[Curso]) -> bool:
    """True si el curso existe y está en el catálogo (HU-05 / HU-06)."""
    return bool(curso) and (curso.estado_curso or "").upper() == PUBLICADO


def puede_publicarse(db: Session, curso: Curso) -> bool:
    """HU-05 esc. 3: información completa + profesor asignado + al menos una lección."""
    info_completa = bool(
        (curso.nombre_curso or "").strip()
        and (curso.descripcion_curso or "").strip()
        and curso.duracion_horas
        and curso.id_categoria
        and curso.id_docente
    )
    tiene_lecciones = db.query(Leccion).filter(Leccion.id_curso == curso.id_curso).count() > 0
    return info_completa and tiene_lecciones


def actualizar(db: Session, id_curso: UUID, usuario: Usuario, **cambios) -> Optional[Curso]:
    curso = obtener_por_id(db, id_curso)
    if not curso:
        return None
    exigir_gestion_curso(usuario, curso)

    nuevo_estado = cambios.pop("estado_curso", None)
    if nuevo_estado is not None:
        nuevo_estado = nuevo_estado.strip().upper()
        if nuevo_estado not in ESTADOS_CURSO:
            raise ValueError("El estado del curso debe ser BORRADOR o PUBLICADO")
        if nuevo_estado != (curso.estado_curso or "").upper() and not es_admin(usuario):
            raise PermissionError("Solo el administrador puede publicar u ocultar un curso")  # HU-05

    if "id_docente" in cambios:
        if not es_admin(usuario):
            cambios.pop("id_docente")  # el docente no se puede quitar ni pasar el curso a otro
        else:
            _validar_docente(db, cambios["id_docente"])
    if cambios.get("nombre_curso") and _nombre_en_uso(db, cambios["nombre_curso"], excepto=id_curso):
        raise ValueError("El curso ya existe")
    if cambios.get("id_categoria") and not categoria_services.obtener_por_id(db, cambios["id_categoria"]):
        raise ValueError("La categoría no existe")

    # RF-07: detalle de lo que cambia (incluido el estado) antes de aplicarlo
    detalle, cambio = servicio_historial.describir_cambios(curso, dict(cambios, estado_curso=nuevo_estado))

    for campo, valor in cambios.items():
        if valor is not None and hasattr(curso, campo):
            setattr(curso, campo, valor.strip() if isinstance(valor, str) else valor)

    if nuevo_estado is not None:
        if nuevo_estado == PUBLICADO and not puede_publicarse(db, curso):
            db.rollback()
            raise ValueError(MENSAJE_NO_PUBLICABLE)
        curso.estado_curso = nuevo_estado

    if cambio:
        servicio_historial.registrar(db, id_usuario=usuario.id_usuario, entidad="CURSO", id_registro=curso.id_curso,
                                     nombre_registro=curso.nombre_curso, accion=servicio_historial.ACTUALIZAR, detalle=detalle)
    curso.id_usuario_edita = usuario.id_usuario
    db.commit()
    db.refresh(curso)
    return curso


def eliminar(db: Session, id_curso: UUID, usuario: Usuario) -> bool:
    curso = obtener_por_id(db, id_curso)
    if not curso:
        return False
    exigir_gestion_curso(usuario, curso)
    tiene_lecciones = db.query(Leccion).filter(Leccion.id_curso == id_curso).first()
    tiene_inscritos = db.query(Inscripcion).filter(Inscripcion.id_curso == id_curso).first()
    if tiene_lecciones or tiene_inscritos:
        raise ValueError(
            "El curso tiene lecciones o estudiantes inscritos y no se puede eliminar. Páselo a BORRADOR para ocultarlo"
        )
    servicio_historial.registrar(db, id_usuario=usuario.id_usuario, entidad="CURSO", id_registro=curso.id_curso,
                                 nombre_registro=curso.nombre_curso, accion=servicio_historial.ELIMINAR,
                                 detalle=f"Curso eliminado: {curso.nombre_curso}")  # RF-07
    db.delete(curso)
    db.commit()
    return True


def catalogo(db: Session, id_categoria: Optional[UUID] = None) -> List[Curso]:
    """HU-06: cursos PUBLICADOS, con filtro opcional por categoría."""
    # Los cursos viejos en "ACTIVO" ya los pasó a PUBLICADO el script migrardb.py
    consulta = db.query(Curso).filter(Curso.estado_curso == PUBLICADO)
    if id_categoria:
        consulta = consulta.filter(Curso.id_categoria == id_categoria)
    return consulta.order_by(Curso.nombre_curso).all()
