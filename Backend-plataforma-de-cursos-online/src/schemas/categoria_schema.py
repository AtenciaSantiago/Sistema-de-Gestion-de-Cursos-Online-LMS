from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base_schema import EntradaSchema


class CategoriaCreate(EntradaSchema):
    nombre_categoria: str = Field(..., min_length=1, max_length=150)  # HU-04 esc. 1


class CategoriaUpdate(EntradaSchema):
    nombre_categoria: Optional[str] = Field(None, min_length=1, max_length=150)


class CategoriaResponse(BaseModel):
    id_categoria: UUID
    nombre_categoria: str
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
