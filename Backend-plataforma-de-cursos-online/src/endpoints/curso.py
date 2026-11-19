"""
Endpoints de cursos (HU-04 y HU-05). El catálogo público del estudiante está en checkout.py (HU-06).
"""

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.entities.usuario import Usuario
from src.schemas.curso_schema import CursoCreate, CursoResponse, CursoUpdate
from src.schemas.response_schema import RespuestaAPI
from src.services import curso as services_curso
from src.services import inscripcion as services_inscripcion
from src.services.permisos import puede_gestionar_curso

from .deps import ADMIN_O_DOCENTE, DbSession

router = APIRouter(prefix="/cursos", tags=["cursos"])


def _no_existe() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado")


@router.get("", response_model=List[CursoResponse])
def listar_cursos(db: DbSession, skip: int = 0, limit: int = 100, usuario: Usuario = ADMIN_O_DOCENTE):
    """El Admin ve todos los cursos; el Docente solo los suyos (HU-07)."""
    return services_curso.obtener_para_usuario(db, usuario, skip, limit)


@router.get("/{id_curso}", response_model=CursoResponse)
def obtener_curso(db: DbSession, id_curso: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    curso = services_curso.obtener_por_id(db, id_curso)
    if not curso or not puede_gestionar_curso(usuario, curso):
        raise _no_existe()
    return curso


@router.post("", response_model=CursoResponse, status_code=status.HTTP_201_CREATED)
def crear_curso(db: DbSession, dato: CursoCreate, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        return services_curso.crear(
            db,
            usuario,
            id_categoria=dato.id_categoria,
            nombre_curso=dato.nombre_curso,
            descripcion_curso=dato.descripcion_curso,
            duracion_horas=dato.duracion_horas,
            precio=dato.precio,
            id_docente=dato.id_docente,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{id_curso}", response_model=CursoResponse)
def actualizar_curso(db: DbSession, id_curso: UUID, dato: CursoUpdate, usuario: Usuario = ADMIN_O_DOCENTE):
    """HU-04 esc. 3 (editar) y HU-05 (publicar / pasar a borrador, solo Admin)."""
    try:
        curso = services_curso.actualizar(db, id_curso, usuario, **dato.model_dump(exclude_unset=True))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not curso:
        raise _no_existe()
    return curso


@router.delete("/{id_curso}", response_model=RespuestaAPI)
def eliminar_curso(db: DbSession, id_curso: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        eliminado = services_curso.eliminar(db, id_curso, usuario)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not eliminado:
        raise _no_existe()
    return RespuestaAPI(mensaje="Curso eliminado exitosamente", exito=True)


@router.get("/{id_curso}/estudiantes", response_model=Dict[str, Any])
def estudiantes_matriculados(db: DbSession, id_curso: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    """HU-10: el profesor ve quiénes están matriculados en SU curso y cuánto llevan."""
    curso = services_curso.obtener_por_id(db, id_curso)
    if not curso or not puede_gestionar_curso(usuario, curso):
        raise _no_existe()
    estudiantes = services_inscripcion.estudiantes_del_curso(db, id_curso)
    return {
        "id_curso": curso.id_curso,
        "nombre_curso": curso.nombre_curso,
        "estudiantes": estudiantes,
        "mensaje": None if estudiantes else services_inscripcion.MENSAJE_SIN_ESTUDIANTES,  # HU-10 esc. 2
    }
