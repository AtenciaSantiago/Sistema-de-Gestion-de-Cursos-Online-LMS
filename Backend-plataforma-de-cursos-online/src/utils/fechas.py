"""
Fechas de los filtros de auditoría (pagos RF-11 e historial de cambios RF-07).

El administrador escribe las fechas en hora de Colombia, pero la base de datos
guarda cada registro con su zona horaria (en Neon, en UTC). Si se compara la
fecha "a secas", un pago hecho después de las 7:00 p. m. de Colombia queda con
fecha del día siguiente en UTC y el filtro de "hoy" no lo muestra.

Por eso el inicio y el fin del día se calculan en hora de Colombia y se
convierten a UTC antes de consultar.
"""

from datetime import date, datetime, time, timedelta, timezone

ZONA_COLOMBIA = timezone(timedelta(hours=-5))  # Colombia no tiene horario de verano


def hoy_en_colombia() -> date:
    return datetime.now(ZONA_COLOMBIA).date()


def inicio_del_dia(dia: date) -> datetime:
    """Las 00:00 de ese día en Colombia, expresadas en UTC."""
    return datetime.combine(dia, time.min, tzinfo=ZONA_COLOMBIA).astimezone(timezone.utc)


def fin_del_dia(dia: date) -> datetime:
    """Las 00:00 del día siguiente en Colombia (el filtro "hasta" incluye todo el día)."""
    return inicio_del_dia(dia + timedelta(days=1))
