"""Categorías de cursos (HU-04 esc. 1). Las ven todos; las crean el Admin o el Docente y solo el Admin las edita o borra (RN-02)."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.entities.Curso import Curso
from src.entities.categoria import Categoria
from src.services import historial as servicio_historial


def _nombre_en_uso(db: Session, nombre: str, excepto: Optional[UUID] = None) -> bool:
    consulta = db.query(Categoria).filter(func.lower(Categoria.nombre_categoria) == nombre.strip().lower())
    if excepto:
        consulta = consulta.filter(Categoria.id_categoria != excepto)
    return consulta.first() is not None


def crear(db: Session, nombre_categoria: str, id_usuario_creacion: UUID) -> Categoria:
    if _nombre_en_uso(db, nombre_categoria):
        raise ValueError("La categoría ya existe")
    categoria = Categoria(nombre_categoria=nombre_categoria.strip(), id_usuario_creacion=id_usuario_creacion)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def obtener_por_id(db: Session, id_categoria: UUID) -> Optional[Categoria]:
    return db.query(Categoria).filter(Categoria.id_categoria == id_categoria).first()


def obtener_todos(db: Session, skip: int = 0, limit: int = 100) -> List[Categoria]:
    return db.query(Categoria).order_by(Categoria.nombre_categoria).offset(skip).limit(limit).all()


def actualizar(db: Session, id_categoria: UUID, id_usuario_edita: UUID, nombre_categoria: Optional[str] = None) -> Optional[Categoria]:
    categoria = obtener_por_id(db, id_categoria)
    if not categoria:
        return None
    if nombre_categoria is not None:
        if _nombre_en_uso(db, nombre_categoria, excepto=id_categoria):
            raise ValueError("La categoría ya existe")
        detalle, cambio = servicio_historial.describir_cambios(categoria, {"nombre_categoria": nombre_categoria})
        if cambio:  # RF-07: queda quién, cuándo y qué cambió
            servicio_historial.registrar(db, id_usuario=id_usuario_edita, entidad="CATEGORIA", id_registro=categoria.id_categoria,
                                         nombre_registro=categoria.nombre_categoria, accion=servicio_historial.ACTUALIZAR, detalle=detalle)
        categoria.nombre_categoria = nombre_categoria.strip()
    categoria.id_usuario_edita = id_usuario_edita
    db.commit()
    db.refresh(categoria)
    return categoria


def eliminar(db: Session, id_categoria: UUID, id_usuario: UUID) -> bool:
    categoria = obtener_por_id(db, id_categoria)
    if not categoria:
        return False
    # Entregable 2: antes borrar una categoría con cursos reventaba el servidor (error 500)
    if db.query(Curso).filter(Curso.id_categoria == id_categoria).first():
        raise ValueError("No se puede eliminar la categoría porque tiene cursos asociados")
    servicio_historial.registrar(db, id_usuario=id_usuario, entidad="CATEGORIA", id_registro=categoria.id_categoria,
                                 nombre_registro=categoria.nombre_categoria, accion=servicio_historial.ELIMINAR,
                                 detalle=f"Categoría eliminada: {categoria.nombre_categoria}")  # RF-07
    db.delete(categoria)
    db.commit()
    return True
