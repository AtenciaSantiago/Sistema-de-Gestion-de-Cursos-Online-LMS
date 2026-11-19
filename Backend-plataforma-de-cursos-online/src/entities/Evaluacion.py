import uuid

from sqlalchemy import Column, ForeignKey, String, Float, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.config import Base

# Entregable 2: la nota para aprobar que se usa si la evaluación no trae una propia (escala 0 a 5)
NOTA_MINIMA_POR_DEFECTO = 3.0


class Evaluacion(Base):
    """Modelo de evaluación"""

    __tablename__ = "evaluacion"

    id_evaluacion = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    
    id_leccion = Column(
        UUID(as_uuid=True), ForeignKey("leccion.id_leccion"), nullable=False, unique=True
    )


    nombre_evaluacion = Column(String(150), nullable=False)  # Entregable 2: antes 20 caracteres
    porcentaje = Column(Float, nullable=False)
    # Entregable 2 (HU-14): nota mínima para aprobar ESTA evaluación (escala 0 a 5)
    nota_minima = Column(Float, nullable=False, default=NOTA_MINIMA_POR_DEFECTO, server_default="3.0")
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_edicion = Column(DateTime(timezone=True), onupdate=func.now())
     
    
    id_usuario_creacion = Column(
        UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=False
    )
    id_usuario_edita = Column(
        UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=True
    )

    usuario_creacion = relationship("Usuario", foreign_keys=[id_usuario_creacion])
    usuario_edita = relationship("Usuario", foreign_keys=[id_usuario_edita])
    leccion = relationship("Leccion", foreign_keys=[id_leccion])

    @property
    def nota_para_aprobar(self) -> float:
        """Entregable 2: la regla vive en UN solo lugar; aula, presentación y cierre la usan."""
        return self.nota_minima if self.nota_minima is not None else NOTA_MINIMA_POR_DEFECTO

    def aprueba(self, nota) -> bool:
        """True si esa nota alcanza la mínima de esta evaluación."""
        return nota is not None and nota >= self.nota_para_aprobar
