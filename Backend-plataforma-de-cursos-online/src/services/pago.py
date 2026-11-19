"""
Auditoría de pagos (RF-11).

Entregable 2: los pagos YA NO se crean ni se editan a mano. Los registra el
sistema cuando el estudiante paga en línea (HU-09, services/checkout.py), aprobados
o rechazados. El Admin solo los consulta y filtra; así no se puede inventar un pago.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.Pago import Pago
from src.utils.fechas import fin_del_dia, inicio_del_dia


def obtener_por_id(db: Session, id_pago: UUID) -> Optional[Pago]:
    return db.query(Pago).filter(Pago.id_pago == id_pago).first()


def buscar(
    db: Session,
    id_curso: Optional[UUID] = None,
    id_estudiante: Optional[UUID] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Pago]:
    """RF-11: historial de pagos filtrando por curso, estudiante y rango de fechas."""
    if desde and hasta and desde > hasta:
        raise ValueError("La fecha inicial no puede ser posterior a la fecha final")
    consulta = db.query(Pago)
    if id_curso:
        consulta = consulta.filter(Pago.id_curso == id_curso)
    if id_estudiante:
        consulta = consulta.filter(Pago.id_usuario == id_estudiante)
    if desde:
        consulta = consulta.filter(Pago.fecha_creacion >= inicio_del_dia(desde))
    if hasta:  # incluye todo el día "hasta", en hora de Colombia
        consulta = consulta.filter(Pago.fecha_creacion < fin_del_dia(hasta))
    return consulta.order_by(Pago.fecha_creacion.desc()).offset(skip).limit(limit).all()
