"""
Materiales de estudio de una lección (HU-11 esc. 2): PDF, video, documento o enlace.
RN-03: un material siempre pertenece a una lección que existe.
"""

from typing import List, Optional
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.Leccion import Leccion
from src.entities.Material import Material
from src.entities.usuario import Usuario
from src.schemas.material_schema import TIPOS_MATERIAL
from src.services import leccion as leccion_services
from src.services import historial as servicio_historial
from src.services.permisos import curso_de_leccion, es_admin, exigir_gestion_curso


def _validar_datos(tipo_material: Optional[str], url: Optional[str]) -> None:
    if tipo_material is not None and tipo_material.strip().upper() not in TIPOS_MATERIAL:
        raise ValueError("El tipo de material debe ser PDF, VIDEO, DOCUMENTO o ENLACE")
    enlace = urlparse(url.strip()) if url is not None else None
    if enlace is not None and (enlace.scheme.lower() not in ("http", "https") or not enlace.netloc):
        raise ValueError("El enlace del material debe ser una dirección web completa (http:// o https://)")


def _leccion_permitida(db: Session, usuario: Usuario, id_leccion: UUID) -> Leccion:
    leccion = leccion_services.obtener_por_id(db, id_leccion)
    if not leccion:
        raise ValueError("La lección no existe")  # RN-03
    exigir_gestion_curso(usuario, curso_de_leccion(db, leccion))
    return leccion


def crear(db: Session, usuario: Usuario, id_leccion: UUID, titulo_material: str, tipo_material: str, URL_archivo: str) -> Material:
    _leccion_permitida(db, usuario, id_leccion)
    _validar_datos(tipo_material, URL_archivo)
    material = Material(
        id_leccion=id_leccion,
        titulo_material=titulo_material.strip(),
        tipo_material=tipo_material.strip().upper(),
        URL_archivo=URL_archivo.strip(),
        id_usuario_creacion=usuario.id_usuario,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def obtener_por_id(db: Session, id_material: UUID) -> Optional[Material]:
    return db.query(Material).filter(Material.id_material == id_material).first()


def obtener_para_usuario(db: Session, usuario: Usuario, id_leccion: Optional[UUID] = None) -> List[Material]:
    """El Docente solo ve los materiales de sus cursos."""
    consulta = db.query(Material)
    if not es_admin(usuario):
        ids_lecciones = [l.id_leccion for l in leccion_services.obtener_para_usuario(db, usuario)]
        consulta = consulta.filter(Material.id_leccion.in_(ids_lecciones))
    if id_leccion:
        consulta = consulta.filter(Material.id_leccion == id_leccion)
    return consulta.all()


def actualizar(db: Session, id_material: UUID, usuario: Usuario, **cambios) -> Optional[Material]:
    material = obtener_por_id(db, id_material)
    if not material:
        return None
    _leccion_permitida(db, usuario, material.id_leccion)
    if cambios.get("id_leccion"):
        _leccion_permitida(db, usuario, cambios["id_leccion"])  # también debe poder usar la lección nueva
    _validar_datos(cambios.get("tipo_material"), cambios.get("URL_archivo"))

    if cambios.get("tipo_material"):
        cambios["tipo_material"] = cambios["tipo_material"].strip().upper()
    detalle, cambio = servicio_historial.describir_cambios(material, cambios)  # RF-07
    for campo, valor in cambios.items():
        if valor is not None:
            setattr(material, campo, valor.strip() if isinstance(valor, str) else valor)
    if cambio:
        servicio_historial.registrar(db, id_usuario=usuario.id_usuario, entidad="MATERIAL", id_registro=material.id_material,
                                     nombre_registro=material.titulo_material, accion=servicio_historial.ACTUALIZAR, detalle=detalle)
    material.id_usuario_edita = usuario.id_usuario
    db.commit()
    db.refresh(material)
    return material


def eliminar(db: Session, id_material: UUID, usuario: Usuario) -> bool:
    material = obtener_por_id(db, id_material)
    if not material:
        return False
    _leccion_permitida(db, usuario, material.id_leccion)
    servicio_historial.registrar(db, id_usuario=usuario.id_usuario, entidad="MATERIAL", id_registro=material.id_material,
                                 nombre_registro=material.titulo_material, accion=servicio_historial.ELIMINAR,
                                 detalle=f"Material eliminado: {material.titulo_material} ({material.tipo_material})")  # RF-07
    db.delete(material)
    db.commit()
    return True
