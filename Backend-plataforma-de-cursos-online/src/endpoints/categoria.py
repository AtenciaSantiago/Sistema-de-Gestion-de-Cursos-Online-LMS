"""
Endpoints de categorías (HU-04 esc. 1). Listar es público porque el catálogo filtra por categoría (HU-06).
Crear: Admin o Docente. Editar y eliminar: solo Admin.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.entities.usuario import Usuario
from src.schemas.categoria_schema import CategoriaCreate, CategoriaResponse, CategoriaUpdate
from src.schemas.response_schema import RespuestaAPI
from src.services import categoria as services_categoria

from .deps import ADMIN_O_DOCENTE, SOLO_ADMIN, DbSession

router = APIRouter(prefix="/categorias", tags=["categorias"])


def _no_existe() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")


@router.get("", response_model=List[CategoriaResponse])
def listar_categorias(db: DbSession, skip: int = 0, limit: int = 100):
    return services_categoria.obtener_todos(db, skip, limit)


@router.get("/{id_categoria}", response_model=CategoriaResponse)
def obtener_categoria(db: DbSession, id_categoria: UUID):
    categoria = services_categoria.obtener_por_id(db, id_categoria)
    if not categoria:
        raise _no_existe()
    return categoria


@router.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_categoria(db: DbSession, dato: CategoriaCreate, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        return services_categoria.crear(db, nombre_categoria=dato.nombre_categoria, id_usuario_creacion=usuario.id_usuario)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{id_categoria}", response_model=CategoriaResponse)
def actualizar_categoria(db: DbSession, id_categoria: UUID, dato: CategoriaUpdate, usuario: Usuario = SOLO_ADMIN):
    # El E1 (HU-04 esc. 1) deja CREAR categorías al Admin o al Instructor; cambiarlas o borrarlas
    # afecta los cursos de todos los profesores, por eso solo lo hace el Admin
    # Entregable 2: antes este endpoint fallaba (error 500) si no se mandaba id_usuario_edita
    try:
        categoria = services_categoria.actualizar(
            db, id_categoria, id_usuario_edita=usuario.id_usuario, nombre_categoria=dato.nombre_categoria
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not categoria:
        raise _no_existe()
    return categoria


@router.delete("/{id_categoria}", response_model=RespuestaAPI)
def eliminar_categoria(db: DbSession, id_categoria: UUID, admin: Usuario = SOLO_ADMIN):
    try:
        eliminado = services_categoria.eliminar(db, id_categoria, id_usuario=admin.id_usuario)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not eliminado:
        raise _no_existe()
    return RespuestaAPI(mensaje="Categoría eliminada exitosamente", exito=True)
