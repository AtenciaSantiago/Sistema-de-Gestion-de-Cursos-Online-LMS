"""
Certificados (HU-13, RF-16, RF-17).
- Los emite ÚNICAMENTE el sistema al aprobar el curso (ObservadorCertificado, HU-16, RN-04);
  no existe emisión manual: el Arreglo del E1 eliminó la HU-08 y RF-16 da como roles «Estudiante, Sistema».
- El Admin solo los consulta.
- Cualquiera puede verificar un certificado con su código (RF-17).
- No se editan ni se borran: un certificado emitido es inalterable (RU-04).
"""

from typing import List

from fastapi import APIRouter, HTTPException, status
from uuid import UUID

from src.schemas.certificado_schema import CertificadoResponse
from src.services import certificado as services_certificado

from .deps import SOLO_ADMIN, DbSession

router = APIRouter(prefix="/certificados", tags=["certificados"])


@router.get("/verificar/{codigo}")
def verificar_certificado(db: DbSession, codigo: str):
    """Público: escribe el código que aparece en el PDF (ej. CERT-2026-1A2B3C)."""
    datos = services_certificado.verificar(db, codigo)
    if not datos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe un certificado con ese código")
    return datos


@router.get("", response_model=List[CertificadoResponse], dependencies=[SOLO_ADMIN])
def listar_certificados(db: DbSession, skip: int = 0, limit: int = 100):
    return services_certificado.obtener_todos(db, skip, limit)


@router.get("/{id_certificado}", response_model=CertificadoResponse, dependencies=[SOLO_ADMIN])
def obtener_certificado(db: DbSession, id_certificado: UUID):
    certificado = services_certificado.obtener_por_id(db, id_certificado)
    if not certificado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificado no encontrado")
    return certificado

