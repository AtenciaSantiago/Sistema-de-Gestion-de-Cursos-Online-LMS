"""
RF-07 Control de cambios (P7): historial de modificaciones de los contenidos activos.

Cada servicio que modifica o elimina un curso, lección, material, evaluación, pregunta o
categoría llama a registrar(...) ANTES de hacer commit, así el cambio y su registro quedan
en la misma transacción (o se guardan los dos o no se guarda ninguno).

No usa ningún patrón GoF: es una llamada simple de servicio (matriz GoF, fila 8).
"""

from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.historial_cambio import HistorialCambio
from src.utils.fechas import fin_del_dia, inicio_del_dia

ACTUALIZAR = "ACTUALIZAR"
ELIMINAR = "ELIMINAR"
ENTIDADES = ("CURSO", "LECCION", "MATERIAL", "EVALUACION", "PREGUNTA", "CATEGORIA")


def _texto(valor: Any) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, (list, tuple)):
        return ", ".join(str(v) for v in valor)
    return str(valor)


def describir_cambios(objeto: Any, cambios: Dict[str, Any], ignorar: Iterable[str] = ()) -> Tuple[str, bool]:
    """
    Compara los valores actuales del objeto con los nuevos y arma el detalle
    «campo: antes -> después» solo con lo que de verdad cambia.
    Devuelve (detalle, hubo_cambios). Se llama ANTES de aplicar los cambios.
    """
    lineas: List[str] = []
    for campo, nuevo in cambios.items():
        if nuevo is None or campo in ignorar or not hasattr(objeto, campo):
            continue
        actual = getattr(objeto, campo)
        nuevo_norm = nuevo.strip() if isinstance(nuevo, str) else nuevo
        if _texto(actual) != _texto(nuevo_norm):
            lineas.append(f"{campo}: {_texto(actual)} -> {_texto(nuevo_norm)}")
    return ("; ".join(lineas), bool(lineas))


def registrar(
    db: Session,
    *,
    id_usuario: UUID,
    entidad: str,
    id_registro: UUID,
    nombre_registro: Optional[str],
    accion: str,
    detalle: str,
) -> HistorialCambio:
    """Agrega el registro a la sesión (sin commit: lo hace el servicio que llama)."""
    if entidad not in ENTIDADES:
        raise ValueError(f"Entidad desconocida para el historial: {entidad}")
    if accion not in (ACTUALIZAR, ELIMINAR):
        raise ValueError(f"Acción desconocida para el historial: {accion}")
    registro = HistorialCambio(
        id_usuario=id_usuario,
        entidad=entidad,
        id_registro=id_registro,
        nombre_registro=(nombre_registro or "")[:255] or None,
        accion=accion,
        detalle=detalle or "(sin cambios en los campos)",
    )
    db.add(registro)
    return registro


def buscar(
    db: Session,
    entidad: Optional[str] = None,
    id_usuario: Optional[UUID] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    skip: int = 0,
    limit: int = 200,
) -> List[HistorialCambio]:
    """Consulta del Administrador con filtros opcionales (misma convención de fechas que la auditoría de pagos)."""
    if desde and hasta and desde > hasta:
        raise ValueError("La fecha inicial no puede ser mayor que la fecha final")
    consulta = db.query(HistorialCambio)
    if entidad:
        entidad = entidad.strip().upper()
        if entidad not in ENTIDADES:
            raise ValueError("La entidad debe ser una de: " + ", ".join(ENTIDADES))
        consulta = consulta.filter(HistorialCambio.entidad == entidad)
    if id_usuario:
        consulta = consulta.filter(HistorialCambio.id_usuario == id_usuario)
    if desde:
        consulta = consulta.filter(HistorialCambio.fecha >= inicio_del_dia(desde))
    if hasta:  # incluye todo el día "hasta", en hora de Colombia
        consulta = consulta.filter(HistorialCambio.fecha < fin_del_dia(hasta))
    return consulta.order_by(HistorialCambio.fecha.desc()).offset(skip).limit(limit).all()
