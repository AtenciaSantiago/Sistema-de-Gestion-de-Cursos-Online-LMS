"""Auditoría de pagos para el Administrador (RF-11). Solo lectura."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.schemas.pago_schema import PagoResponse
from src.services import pago as services_pago

from .deps import SOLO_ADMIN, DbSession

router = APIRouter(prefix="/pago", tags=["pagos"], dependencies=[SOLO_ADMIN])


@router.get("", response_model=List[PagoResponse])
def listar_pagos(
    db: DbSession,
    id_curso: Optional[UUID] = None,
    id_estudiante: Optional[UUID] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
):
    try:
        return services_pago.buscar(db, id_curso, id_estudiante, desde, hasta, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{id_pago}", response_model=PagoResponse)
def obtener_pago(db: DbSession, id_pago: UUID):
    pago = services_pago.obtener_por_id(db, id_pago)
    if not pago:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")
    return pago
