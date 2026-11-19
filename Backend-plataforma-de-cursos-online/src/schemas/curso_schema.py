from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base_schema import EntradaSchema

# HU-05: los dos estados de un curso. Solo los PUBLICADOS salen en el catálogo.
ESTADOS_CURSO = ("BORRADOR", "PUBLICADO")


class CursoCreate(EntradaSchema):
    # HU-04 esc. 2: nombre, descripción, duración, categoría y profesor asignado son obligatorios
    id_categoria: UUID
    nombre_curso: str = Field(..., min_length=1, max_length=100)
    descripcion_curso: str = Field(..., min_length=1)
    duracion_horas: int = Field(..., gt=0)
    precio: float = Field(0.0, ge=0)  # Entregable 2 (HU-09)
    # Si lo crea un Docente, el profesor es él mismo. Si lo crea el Admin, debe escogerlo.
    id_docente: Optional[UUID] = None
    # Se ignora: todo curso nuevo nace en BORRADOR (HU-04 esc. 2). Se deja para no romper el front.
    estado_curso: Optional[str] = None


class CursoUpdate(EntradaSchema):
    id_categoria: Optional[UUID] = None
    nombre_curso: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion_curso: Optional[str] = Field(None, min_length=1)
    duracion_horas: Optional[int] = Field(None, gt=0)
    precio: Optional[float] = Field(None, ge=0)
    id_docente: Optional[UUID] = None
    estado_curso: Optional[str] = None  # BORRADOR / PUBLICADO (solo el Admin, HU-05)


class CursoResponse(BaseModel):
    id_curso: UUID
    id_categoria: UUID
    nombre_categoria: Optional[str] = None
    nombre_curso: str
    duracion_horas: int
    estado_curso: str
    descripcion_curso: Optional[str] = None
    precio: Optional[float] = 0.0
    id_docente: Optional[UUID] = None
    nombre_docente: Optional[str] = None
    numero_lecciones: int = 0  # HU-07 esc. 1: nombre, categoría, número de lecciones y estado
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
