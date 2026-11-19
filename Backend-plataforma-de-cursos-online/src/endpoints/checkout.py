"""
Endpoints del estudiante para ver el catálogo y pagar un curso (HU-06 y HU-09).
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.entities.usuario import Usuario
from src.patrones.pagos import PasarelaPago, PasarelaSimuladaAdapter
from src.schemas.checkout_schema import CheckoutRequest, CheckoutResponse
from src.schemas.curso_schema import CursoResponse
from src.services import checkout as servicio_checkout
from src.services import curso as servicio_cursos

from .deps import SOLO_ESTUDIANTE, DbSession

router = APIRouter(tags=["catálogo y pago (estudiante)"])


def obtener_pasarela() -> PasarelaPago:
    """
    Aquí se decide QUÉ pasarela usa el sistema (inyección de dependencias).
    Hoy es la simulada; para una real solo se cambia esta línea.
    En las pruebas se reemplaza por una pasarela falsa.
    """
    return PasarelaSimuladaAdapter()


@router.get("/catalogo", response_model=List[CursoResponse])
def ver_catalogo(db: DbSession, id_categoria: Optional[UUID] = None):
    """HU-06: lista de cursos publicados (filtro opcional por categoría)."""
    return servicio_cursos.catalogo(db, id_categoria)


@router.post("/checkout/cursos/{id_curso}", response_model=CheckoutResponse)
def pagar_curso(
    db: DbSession,
    id_curso: UUID,
    dato: CheckoutRequest,
    usuario: Usuario = SOLO_ESTUDIANTE,
    pasarela: PasarelaPago = Depends(obtener_pasarela),
):
    """HU-09: el estudiante paga y, si la pasarela aprueba, queda matriculado solo (RN-01)."""
    datos_pago = dato.model_dump(exclude={"metodo_pago"}, exclude_none=True)
    try:
        r = servicio_checkout.pagar_curso(
            db, usuario.id_usuario, id_curso, dato.metodo_pago, datos_pago, pasarela
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return CheckoutResponse(
        aprobado=r.resultado.aprobado,
        mensaje=r.resultado.mensaje,
        referencia=r.resultado.referencia,
        id_pago=r.pago.id_pago,
        monto=r.pago.monto,
        metodo_pago=r.pago.metodo_pago,
        id_inscripcion=r.inscripcion.id_inscripcion,
        estado_inscripcion=str(r.inscripcion.estado_inscripcion),
    )
