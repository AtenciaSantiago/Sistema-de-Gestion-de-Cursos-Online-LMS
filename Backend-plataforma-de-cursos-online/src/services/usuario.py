"""
CRUD para la entidad Usuario.
Incluye creación, login (verificación de contraseña) y operaciones básicas.
"""

import bcrypt
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session
from src.entities.usuario import Usuario

MENSAJE_CORREO_REPETIDO = "El correo electrónico ya se encuentra registrado en la plataforma"  # HU-02 esc. 2 (registro público)
MENSAJE_CORREO_REPETIDO_ADMIN = "El correo electrónico ya se encuentra registrado en el sistema"  # HU-03 esc. 4 (lo crea el administrador)
MENSAJE_CUENTA_DESACTIVADA = "Su cuenta se encuentra desactivada. Contacte al administrador"  # HU-01 esc. 3


class CuentaDesactivadaError(Exception):
    """La contraseña es correcta pero el administrador desactivó la cuenta."""


def _hash_contrasena(contrasena: str) -> str:
    """Cifra la contraseña con bcrypt (RNF-03): en la base nunca queda la contraseña real."""
    return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()

def crear(
    db: Session,
    nombre_usuario: str,
    tipo_documento: str,
    documento_identidad: str,
    email: str,
    contrasena: str,
    rol: str = "Estudiante",
    activo: bool = True,
    creado_por_admin: bool = False,
) -> Usuario:
    """Crea un nuevo usuario. La contraseña se hashea antes de guardar.

    creado_por_admin cambia el mensaje del correo repetido: la HU-02 (registro público) dice
    «en la plataforma» y la HU-03 esc. 4 (el administrador crea la cuenta) dice «en el sistema».
    """
    nombre_usuario_existente = (
        db.query(Usuario)
        .filter(Usuario.nombre_usuario == nombre_usuario.strip())
        .first()
    )
    if nombre_usuario_existente:
        raise ValueError("El nombre de usuario ya existe")
    # Entregable 2: antes un correo o documento repetido reventaba el servidor (error 500)
    if _correo_en_uso(db, email):
        raise ValueError(MENSAJE_CORREO_REPETIDO_ADMIN if creado_por_admin else MENSAJE_CORREO_REPETIDO)
    if _documento_en_uso(db, documento_identidad):
        raise ValueError("El número de documento ya se encuentra registrado en la plataforma")
    usuario = Usuario(
        nombre_usuario=nombre_usuario.strip(),
        tipo_documento=tipo_documento.strip(),
        documento_identidad=documento_identidad.strip(),
        email=email.strip().lower(),
        contrasena=_hash_contrasena(contrasena),
        rol=rol.strip(),
        activo=activo,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario

def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
    return bcrypt.checkpw(
        contrasena_plana.encode(),
        contrasena_hash.encode()
    )

def _correo_en_uso(db: Session, email: str, excepto: Optional[UUID] = None) -> bool:
    consulta = db.query(Usuario).filter(func.lower(Usuario.email) == email.strip().lower())
    if excepto:
        consulta = consulta.filter(Usuario.id_usuario != excepto)
    return consulta.first() is not None


def _documento_en_uso(db: Session, documento: str, excepto: Optional[UUID] = None) -> bool:
    consulta = db.query(Usuario).filter(Usuario.documento_identidad == documento.strip())
    if excepto:
        consulta = consulta.filter(Usuario.id_usuario != excepto)
    return consulta.first() is not None


def login(db: Session, usuario_o_correo: str, contrasena: str) -> Optional[Usuario]:
    """
    HU-01: verifica las credenciales con el correo electrónico o con el nombre de usuario.
    - Devuelve el Usuario si todo está bien.
    - Devuelve None si el usuario no existe o la contraseña está mal (el endpoint
      responde "Credenciales inválidas" sin decir cuál de los dos falló).
    - Lanza CuentaDesactivadaError si la contraseña es correcta pero la cuenta está inactiva.
    """
    dato = usuario_o_correo.strip()
    if "@" in dato:
        usuario = db.query(Usuario).filter(func.lower(Usuario.email) == dato.lower()).first()
    else:
        usuario = obtener_por_nombre_usuario(db, dato)
    if not usuario or not verificar_contrasena(contrasena, usuario.contrasena):
        return None
    if not usuario.activo:
        raise CuentaDesactivadaError(MENSAJE_CUENTA_DESACTIVADA)
    return usuario

def obtener_por_id(db: Session, id_usuario: UUID) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()

def obtener_por_nombre_usuario(db: Session, nombre_usuario: str) -> Optional[Usuario]:
    return (
        db.query(Usuario)
        .filter(Usuario.nombre_usuario == nombre_usuario.strip())
        .first()
    )

def obtener_todos(db: Session, skip: int = 0, limit: int = 100) -> List[Usuario]:
    return db.query(Usuario).order_by(Usuario.nombre_usuario).offset(skip).limit(limit).all()

def hay_usuarios(db: Session) -> bool:
    """Indica si existe al menos un usuario (para mostrar opción de registro)."""
    return db.query(Usuario).first() is not None

def actualizar(
    db: Session,
    id_usuario: UUID,
    *,
    nombre_usuario: Optional[str] = None,
    tipo_documento: Optional[str] = None,
    documento_identidad: Optional[str] = None,
    email: Optional[str] = None,
    contrasena: Optional[str] = None,
    rol: Optional[str] = None,
    activo: Optional[bool] = None,
) -> Optional[Usuario]:
    usuario = obtener_por_id(db, id_usuario)
    if not usuario:
        return None
    # Entregable 2: al editar tampoco se puede repetir el correo ni el documento de otro usuario
    if email is not None and _correo_en_uso(db, email, excepto=id_usuario):
        raise ValueError(MENSAJE_CORREO_REPETIDO)
    if documento_identidad is not None and _documento_en_uso(db, documento_identidad, excepto=id_usuario):
        raise ValueError("El número de documento ya se encuentra registrado en la plataforma")
    if nombre_usuario is not None:
        otro = obtener_por_nombre_usuario(db, nombre_usuario)
        if otro and otro.id_usuario != id_usuario:
            raise ValueError("El nombre de usuario ya existe")
        usuario.nombre_usuario = nombre_usuario.strip()
    if tipo_documento is not None:
        usuario.tipo_documento = tipo_documento.strip()
    if documento_identidad is not None:
        usuario.documento_identidad = documento_identidad.strip()
    if email is not None:
        usuario.email = email.strip().lower()
    if contrasena is not None:
        usuario.contrasena = _hash_contrasena(contrasena)
    if rol is not None:
        usuario.rol = rol.strip()
    if activo is not None:
        usuario.activo = activo
    db.commit()
    db.refresh(usuario)
    return usuario

def eliminar(db: Session, id_usuario: UUID) -> bool:
    usuario = obtener_por_id(db, id_usuario)
    if not usuario:
        return False
    db.delete(usuario)
    db.commit()
    return True