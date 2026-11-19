import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.config import Base


class Pregunta(Base):
    """
    Tabla de preguntas de una evaluación (HU-14).
    Cada evaluación tiene varias preguntas; el tipo dice qué creador
    de la Factory se usa para armarla y calificarla.
    """

    __tablename__ = "pregunta"

    id_pregunta = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    id_evaluacion = Column(
        UUID(as_uuid=True), ForeignKey("evaluacion.id_evaluacion"), nullable=False, index=True
    )
    tipo = Column(String(30), nullable=False)  # OPCION_MULTIPLE o VERDADERO_FALSO
    enunciado = Column(Text, nullable=False)
    opciones = Column(JSON, nullable=False, default=list)  # lista de textos que ve el estudiante
    respuesta_correcta = Column(String(255), nullable=False)  # la clave; nunca se le envía al estudiante
    orden = Column(Integer, nullable=False, default=1)

    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    id_usuario_creacion = Column(UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=False)

    evaluacion = relationship("Evaluacion", foreign_keys=[id_evaluacion])
