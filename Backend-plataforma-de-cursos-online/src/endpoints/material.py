"""Endpoints de materiales de estudio (HU-11 esc. 2)."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.entities.usuario import Usuario
from src.schemas.material_schema import MaterialCreate, MaterialResponse, MaterialUpdate
from src.schemas.response_schema import RespuestaAPI
from src.services import material as services_material
from src.services.permisos import curso_de_leccion, puede_gestionar_curso
from src.services.leccion import obtener_por_id as obtener_leccion

from .deps import ADMIN_O_DOCENTE, DbSession

router = APIRouter(prefix="/material", tags=["materiales"])


def _no_existe() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material no encontrado")


@router.get("", response_model=List[MaterialResponse])
def listar_materiales(db: DbSession, id_leccion: Optional[UUID] = None, usuario: Usuario = ADMIN_O_DOCENTE):
    return services_material.obtener_para_usuario(db, usuario, id_leccion)


@router.get("/{id_material}", response_model=MaterialResponse)
def obtener_material(db: DbSession, id_material: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    material = services_material.obtener_por_id(db, id_material)
    if not material or not puede_gestionar_curso(usuario, curso_de_leccion(db, obtener_leccion(db, material.id_leccion))):
        raise _no_existe()
    return material


@router.post("", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def crear_material(db: DbSession, dato: MaterialCreate, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        return services_material.crear(
            db,
            usuario,
            id_leccion=dato.id_leccion,
            titulo_material=dato.titulo_material,
            tipo_material=dato.tipo_material,
            URL_archivo=dato.URL_archivo,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{id_material}", response_model=MaterialResponse)
def actualizar_material(db: DbSession, id_material: UUID, dato: MaterialUpdate, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        material = services_material.actualizar(db, id_material, usuario, **dato.model_dump(exclude_unset=True))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not material:
        raise _no_existe()
    return material


@router.delete("/{id_material}", response_model=RespuestaAPI)
def eliminar_material(db: DbSession, id_material: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        eliminado = services_material.eliminar(db, id_material, usuario)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    if not eliminado:
        raise _no_existe()
    return RespuestaAPI(mensaje="Material eliminado exitosamente", exito=True)
