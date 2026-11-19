from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base_schema import EntradaSchema


class EvaluacionCreate(EntradaSchema):
    id_leccion: UUID  # RN-03: toda evaluación pertenece a una lección
    nombre_evaluacion: str = Field(..., min_length=1, max_length=150)
    porcentaje: float = Field(..., gt=0, le=100, description="Peso dentro del curso (los del curso suman máximo 100)")
    nota_minima: float = 3.0  # Entregable 2 (HU-14): nota para aprobar, escala 0 a 5 (se valida en el servicio)


class EvaluacionUpdate(EntradaSchema):
    # La evaluación no se cambia de lección; por eso aquí no va id_leccion
    nombre_evaluacion: Optional[str] = Field(None, min_length=1, max_length=150)
    porcentaje: Optional[float] = Field(None, gt=0, le=100)
    nota_minima: Optional[float] = None


class EvaluacionResponse(BaseModel):
    id_evaluacion: UUID
    id_leccion: UUID
    nombre_evaluacion: str
    porcentaje: float
    nota_minima: Optional[float] = None
    id_usuario_creacion: UUID
    id_usuario_edita: Optional[UUID] = None
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
