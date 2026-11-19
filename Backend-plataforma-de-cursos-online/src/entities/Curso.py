import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.config import Base

class Curso(Base):
    """Modelo de curso. Estados: BORRADOR (no se ve en el catálogo) o PUBLICADO (HU-05)."""

    __tablename__ = "curso"

    id_curso = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    id_categoria = Column(
        UUID(as_uuid=True), ForeignKey("categoria.id_categoria"), nullable=False
    )

    nombre_curso = Column(String(100), nullable=False)
    descripcion_curso = Column(Text, nullable=True)
    duracion_horas = Column(Integer, nullable=False)
    estado_curso = Column(String(50), nullable=False)
    # Entregable 2 (HU-09): precio del curso para el pago en línea
    precio = Column(Float, nullable=False, default=0.0, server_default="0")
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_edicion = Column(DateTime(timezone=True), onupdate=func.now())
    # Entregable 2 (HU-04 y HU-05): profesor asignado al curso (usuario con rol Docente).
    # Un curso sin profesor no se puede publicar.
    id_docente = Column(UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=True)
    id_usuario_creacion = Column(
        UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=False
    )
    id_usuario_edita = Column(
        UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=True
    )

    usuario_creacion = relationship("Usuario", foreign_keys=[id_usuario_creacion])
    usuario_edita = relationship("Usuario", foreign_keys=[id_usuario_edita])
    categoria = relationship("Categoria", foreign_keys=[id_categoria])
    docente = relationship("Usuario", foreign_keys=[id_docente])
    # Solo lectura: para contar las lecciones en la lista "Mis cursos asignados" (HU-07)
    lecciones = relationship("Leccion", foreign_keys="Leccion.id_curso", viewonly=True)

    # Para mostrar nombres en pantalla sin que el front tenga que buscar cada id
    @property
    def nombre_docente(self):
        return self.docente.nombre_usuario if self.docente else None

    @property
    def numero_lecciones(self):
        return len(self.lecciones)

    @property
    def nombre_categoria(self):
        return self.categoria.nombre_categoria if self.categoria else None
