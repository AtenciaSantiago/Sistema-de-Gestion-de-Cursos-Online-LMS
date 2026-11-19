from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.base_schema import EntradaSchema


class CheckoutRequest(EntradaSchema):
    """Lo que manda el estudiante al pagar (HU-09)."""

    metodo_pago: str = Field(..., examples=["TARJETA", "PSE"])
    # Tarjeta
    numero_tarjeta: Optional[str] = None
    titular: Optional[str] = None
    # PSE
    banco: Optional[str] = None
    tipo_persona: Optional[str] = None


class CheckoutResponse(BaseModel):
    aprobado: bool
    mensaje: str
    referencia: str
    id_pago: UUID
    monto: float
    metodo_pago: str
    id_inscripcion: UUID
    estado_inscripcion: str
