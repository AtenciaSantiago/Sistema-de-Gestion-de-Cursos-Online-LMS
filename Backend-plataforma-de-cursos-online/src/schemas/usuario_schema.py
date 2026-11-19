from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.schemas.base_schema import EntradaSchema

# Los tres roles del sistema (HU-03). Se escriben siempre igual para que los permisos funcionen.
ROLES_VALIDOS = ("Admin", "Docente", "Estudiante")


def _validar_rol(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None
    for rol in ROLES_VALIDOS:
        if valor.strip().lower() == rol.lower():
            return rol
    raise ValueError("El rol debe ser Admin, Docente o Estudiante")


class UsuarioCreate(EntradaSchema):
    # HU-02 esc. 3: no se aceptan campos vacíos ni correos con formato inválido
    nombre_usuario: str = Field(..., min_length=1, max_length=150, pattern=r"^[^@]+$")  # sin "@" para no confundirlo con un correo al iniciar sesión
    tipo_documento: str = Field(..., min_length=1, max_length=50)
    documento_identidad: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    contrasena: str = Field(..., min_length=8, description="Mínimo 8 caracteres")
    rol: str = "Estudiante"
    activo: bool = True

    _rol_valido = field_validator("rol")(_validar_rol)


class UsuarioUpdate(EntradaSchema):
    nombre_usuario: Optional[str] = Field(None, min_length=1, max_length=150, pattern=r"^[^@]+$")
    tipo_documento: Optional[str] = Field(None, min_length=1, max_length=50)
    documento_identidad: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    contrasena: Optional[str] = Field(None, min_length=8)
    rol: Optional[str] = None
    activo: Optional[bool] = None

    _rol_valido = field_validator("rol")(_validar_rol)

class UsuarioResponse(BaseModel):
    id_usuario: UUID
    nombre_usuario: str
    tipo_documento: str
    documento_identidad: str
    email: EmailStr
    rol: str
    activo: bool
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UsuarioLogin(EntradaSchema):
    # HU-01: se puede escribir el correo electrónico o el nombre de usuario
    nombre_usuario: str = Field(..., min_length=1, description="Correo electrónico o nombre de usuario")
    contrasena: str = Field(..., min_length=1)