from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base_schema import EntradaSchema


class LeccionCreate(EntradaSchema):
    id_curso: UUID
    # HU-11 esc. 4: título y número de orden obligatorios (el servicio da el mensaje de la HU)
    titulo_leccion: Optional[str] = Field(None, max_length=150)
    descripcion_leccion: Optional[str] = None
    orden: Optional[int] = None
    duracion_horas: int = Field(1, gt=0)


class LeccionUpdate(EntradaSchema):
    # La lección no se puede pasar a otro curso; por eso aquí no va id_curso
    titulo_leccion: Optional[str] = Field(None, max_length=150)
    descripcion_leccion: Optional[str] = None
    orden: Optional[int] = None  # HU-11 esc. 3: reordenar
    duracion_horas: Optional[int] = Field(None, gt=0)


class LeccionResponse(BaseModel):
    id_curso: UUID
    id_leccion: UUID
    titulo_leccion: str
    descripcion_leccion: Optional[str] = None
    orden: int
    duracion_horas: int
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
