"""
Consulta de calificaciones (RF-13).

Entregable 2: las notas YA NO se escriben a mano. Las pone el sistema cuando el
estudiante presenta la evaluación (HU-15, calificación automática) y cada intento
queda guardado (RF-13). Así nadie puede subir o bajar una nota sin dejar rastro.
"""

from typing import List

from sqlalchemy.orm import Session

from src.entities.Evaluacion import Evaluacion
from src.entities.calificacion import Calificacion
from src.entities.usuario import Usuario
from src.services import evaluacion as evaluacion_services
from src.services.permisos import es_admin


def obtener_para_usuario(db: Session, usuario: Usuario, skip: int = 0, limit: int = 100) -> List[Calificacion]:
    """El Admin ve todas; el Docente solo las de las evaluaciones de sus cursos."""
    consulta = db.query(Calificacion)
    if not es_admin(usuario):
        ids = [e.id_evaluacion for e in evaluacion_services.obtener_para_usuario(db, usuario)]
        consulta = consulta.filter(Calificacion.id_evaluacion.in_(ids))
    return consulta.join(Evaluacion).order_by(Evaluacion.nombre_evaluacion).offset(skip).limit(limit).all()
