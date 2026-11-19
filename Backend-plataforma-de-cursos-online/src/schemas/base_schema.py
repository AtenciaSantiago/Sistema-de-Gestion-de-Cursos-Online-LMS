"""
Entregable 2: base para todo lo que ENTRA a la API (crear, editar, login, pagar...).

Le quita los espacios al inicio y al final a cada texto. Así, si alguien escribe
solo espacios en un campo obligatorio, cuenta como vacío y sale el mensaje
"Por favor complete todos los campos obligatorios" (HU-02 esc. 3, HU-04 esc. 4).
"""

from pydantic import BaseModel, ConfigDict


class EntradaSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
