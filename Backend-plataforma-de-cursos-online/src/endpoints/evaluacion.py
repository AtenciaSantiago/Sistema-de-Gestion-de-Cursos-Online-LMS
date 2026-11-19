"""Endpoints de evaluaciones (HU-14). Las preguntas están en pregunta.py."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.entities.usuario import Usuario
from src.schemas.evaluacion_schema import EvaluacionCreate, EvaluacionResponse, EvaluacionUpdate
from src.schemas.response_schema import RespuestaAPI
from src.services import evaluacion as services_evaluacion
from src.services.permisos import curso_de_evaluacion, puede_gestionar_curso

from .deps import ADMIN_O_DOCENTE, DbSession

router = APIRouter(prefix="/evaluaciones", tags=["evaluaciones"])


def _no_existe() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluación no encontrada")


@router.get("", response_model=List[EvaluacionResponse])
def listar_evaluaciones(db: DbSession, usuario: Usuario = ADMIN_O_DOCENTE):
    return services_evaluacion.obtener_para_usuario(db, usuario)


@router.get("/{id_evaluacion}", response_model=EvaluacionResponse)
def obtener_evaluacion(db: DbSession, id_evaluacion: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    evaluacion = services_evaluacion.obtener_por_id(db, id_evaluacion)
    if not evaluacion or not puede_gestionar_curso(usuario, curso_de_evaluacion(db, evaluacion)):
        raise _no_existe()
    return evaluacion


@router.post("", response_model=EvaluacionResponse, status_code=status.HTTP_201_CREATED)
def crear_evaluacion(db: DbSession, dato: EvaluacionCreate, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        return services_evaluacion.crear(
            db,
            usuario,
            id_leccion=dato.id_leccion,
            nombre_evaluacion=dato.nombre_evaluacion,
            porcentaje=dato.porcentaje,
            nota_minima=dato.nota_minima,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{id_evaluacion}", response_model=EvaluacionResponse)
def actualizar_evaluacion(db: DbSession, id_evaluacion: UUID, dato: EvaluacionUpdate, usuario: Usuario = ADMIN_O_DOCENTE):
    """HU-14 esc. 2: solo mientras ningún estudiante la haya presentado."""
    try:
        evaluacion = services_evaluacion.actualizar(db, id_evaluacion, usuario, **dato.model_dump(exclude_unset=True))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not evaluacion:
        raise _no_existe()
    return evaluacion


@router.delete("/{id_evaluacion}", response_model=RespuestaAPI)
def eliminar_evaluacion(db: DbSession, id_evaluacion: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        eliminado = services_evaluacion.eliminar(db, id_evaluacion, usuario)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not eliminado:
        raise _no_existe()
    return RespuestaAPI(mensaje="Evaluación eliminada exitosamente", exito=True)
