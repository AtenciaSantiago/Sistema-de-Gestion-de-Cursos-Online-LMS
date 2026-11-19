"""Endpoints de lecciones (HU-11)."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.entities.usuario import Usuario
from src.schemas.leccion_schema import LeccionCreate, LeccionResponse, LeccionUpdate
from src.schemas.response_schema import RespuestaAPI
from src.services import leccion as services_leccion
from src.services.permisos import curso_de_leccion, puede_gestionar_curso

from .deps import ADMIN_O_DOCENTE, DbSession

router = APIRouter(prefix="/lecciones", tags=["lecciones"])


def _no_existe() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lección no encontrada")


@router.get("", response_model=List[LeccionResponse])
def listar_lecciones(db: DbSession, id_curso: Optional[UUID] = None, usuario: Usuario = ADMIN_O_DOCENTE):
    """Árbol de lecciones en orden (opcional: solo las de un curso)."""
    return services_leccion.obtener_para_usuario(db, usuario, id_curso)


@router.get("/{id_leccion}", response_model=LeccionResponse)
def obtener_leccion(db: DbSession, id_leccion: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    leccion = services_leccion.obtener_por_id(db, id_leccion)
    if not leccion or not puede_gestionar_curso(usuario, curso_de_leccion(db, leccion)):
        raise _no_existe()
    return leccion


@router.post("", response_model=LeccionResponse, status_code=status.HTTP_201_CREATED)
def crear_leccion(db: DbSession, dato: LeccionCreate, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        return services_leccion.crear(
            db,
            usuario,
            id_curso=dato.id_curso,
            titulo_leccion=dato.titulo_leccion,
            orden=dato.orden,
            duracion_horas=dato.duracion_horas,
            descripcion_leccion=dato.descripcion_leccion,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{id_leccion}", response_model=LeccionResponse)
def actualizar_leccion(db: DbSession, id_leccion: UUID, dato: LeccionUpdate, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        leccion = services_leccion.actualizar(db, id_leccion, usuario, **dato.model_dump(exclude_unset=True))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not leccion:
        raise _no_existe()
    return leccion


@router.delete("/{id_leccion}", response_model=RespuestaAPI)
def eliminar_leccion(db: DbSession, id_leccion: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        eliminado = services_leccion.eliminar(db, id_leccion, usuario)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not eliminado:
        raise _no_existe()
    return RespuestaAPI(mensaje="Lección eliminada exitosamente", exito=True)
