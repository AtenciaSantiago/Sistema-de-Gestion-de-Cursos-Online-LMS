"""
Servicio de preguntas (HU-14: el docente arma la evaluación).

Aquí NO hay "if tipo == ...": se le pide a la Factory el creador del tipo
y él se encarga de armar y validar la pregunta.
Las preguntas solo se pueden crear, cambiar o borrar mientras ningún estudiante
haya presentado la evaluación (HU-14 esc. 2).
"""

from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.pregunta import Pregunta as PreguntaEntidad
from src.entities.usuario import Usuario
from src.patrones.factory_preguntas import Pregunta, obtener_creador
from src.services import evaluacion as evaluacion_services
from src.services import historial as servicio_historial


def crear(db: Session, id_evaluacion: UUID, datos: Dict, usuario: Usuario) -> PreguntaEntidad:
    if not evaluacion_services.evaluacion_editable(db, id_evaluacion, usuario):
        raise ValueError("La evaluación no existe")

    # 1. La Factory arma la pregunta del tipo correcto y la valida
    creador = obtener_creador(datos.get("tipo"))
    pregunta = creador.preparar_pregunta(datos)

    # 2. Si pasó la validación, la guardamos en la base de datos
    siguiente_orden = db.query(PreguntaEntidad).filter(PreguntaEntidad.id_evaluacion == id_evaluacion).count() + 1
    entidad = PreguntaEntidad(
        id_evaluacion=id_evaluacion,
        tipo=datos["tipo"].upper(),
        enunciado=pregunta.enunciado,
        opciones=pregunta.opciones(),
        respuesta_correcta=pregunta.respuesta_correcta,
        orden=datos.get("orden") or siguiente_orden,
        id_usuario_creacion=usuario.id_usuario,
    )
    db.add(entidad)
    db.commit()
    db.refresh(entidad)
    return entidad


def obtener_por_id(db: Session, id_pregunta: UUID) -> Optional[PreguntaEntidad]:
    return db.query(PreguntaEntidad).filter(PreguntaEntidad.id_pregunta == id_pregunta).first()


def actualizar(db: Session, id_pregunta: UUID, datos: Dict, usuario: Usuario) -> Optional[PreguntaEntidad]:
    """HU-14 esc. 2: cambiar el enunciado, las opciones o la clave."""
    entidad = obtener_por_id(db, id_pregunta)
    if not entidad:
        return None
    evaluacion_services.evaluacion_editable(db, entidad.id_evaluacion, usuario)

    completos = {
        "tipo": entidad.tipo,
        "enunciado": datos.get("enunciado", entidad.enunciado),
        "opciones": datos.get("opciones", entidad.opciones),
        "respuesta_correcta": datos.get("respuesta_correcta", entidad.respuesta_correcta),
    }
    pregunta = obtener_creador(entidad.tipo).preparar_pregunta(completos)  # la Factory vuelve a validar
    nuevos = {"enunciado": pregunta.enunciado, "opciones": pregunta.opciones(),
              "respuesta_correcta": pregunta.respuesta_correcta, "orden": datos.get("orden") or None}
    detalle, cambio = servicio_historial.describir_cambios(entidad, nuevos)  # RF-07
    entidad.enunciado = pregunta.enunciado
    entidad.opciones = pregunta.opciones()
    entidad.respuesta_correcta = pregunta.respuesta_correcta
    if datos.get("orden"):
        entidad.orden = datos["orden"]
    if cambio:
        servicio_historial.registrar(db, id_usuario=usuario.id_usuario, entidad="PREGUNTA", id_registro=entidad.id_pregunta,
                                     nombre_registro=entidad.enunciado, accion=servicio_historial.ACTUALIZAR, detalle=detalle)
    db.commit()
    db.refresh(entidad)
    return entidad


def eliminar(db: Session, id_pregunta: UUID, usuario: Usuario) -> bool:
    entidad = obtener_por_id(db, id_pregunta)
    if not entidad:
        return False
    evaluacion_services.evaluacion_editable(db, entidad.id_evaluacion, usuario)
    servicio_historial.registrar(db, id_usuario=usuario.id_usuario, entidad="PREGUNTA", id_registro=entidad.id_pregunta,
                                 nombre_registro=entidad.enunciado, accion=servicio_historial.ELIMINAR,
                                 detalle=f"Pregunta eliminada: {entidad.enunciado}")  # RF-07
    db.delete(entidad)
    db.commit()
    return True


def listar_por_evaluacion(db: Session, id_evaluacion: UUID) -> List[PreguntaEntidad]:
    return (
        db.query(PreguntaEntidad)
        .filter(PreguntaEntidad.id_evaluacion == id_evaluacion)
        .order_by(PreguntaEntidad.orden)
        .all()
    )


def a_objeto_de_dominio(entidad: PreguntaEntidad) -> Pregunta:
    """Convierte la fila de la base de datos en la pregunta "inteligente" de la Factory."""
    creador = obtener_creador(entidad.tipo)
    return creador.crear_pregunta(
        {
            "enunciado": entidad.enunciado,
            "opciones": entidad.opciones,
            "respuesta_correcta": entidad.respuesta_correcta,
        }
    )
