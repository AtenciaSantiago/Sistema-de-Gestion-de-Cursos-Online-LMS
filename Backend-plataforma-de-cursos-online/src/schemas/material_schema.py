from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base_schema import EntradaSchema

# Tipos de material de la HU-11 esc. 2 (archivos PDF, enlaces a video o documentos)
TIPOS_MATERIAL = ("PDF", "VIDEO", "DOCUMENTO", "ENLACE")


class MaterialCreate(EntradaSchema):
    id_leccion: UUID  # RN-03: todo material pertenece a una lección
    titulo_material: str = Field(..., min_length=1, max_length=150)
    tipo_material: str = Field(..., min_length=1, max_length=20)
    URL_archivo: str = Field(..., min_length=1, max_length=255)


class MaterialUpdate(EntradaSchema):
    id_leccion: Optional[UUID] = None
    titulo_material: Optional[str] = Field(None, min_length=1, max_length=150)
    tipo_material: Optional[str] = Field(None, min_length=1, max_length=20)
    URL_archivo: Optional[str] = Field(None, min_length=1, max_length=255)


class MaterialResponse(BaseModel):
    id_material: UUID
    id_leccion: UUID
    titulo_material: str
    tipo_material: Optional[str] = None
    URL_archivo: str
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
