"""
Endpoints de usuarios: registro (HU-02), inicio de sesión (HU-01) y administración (HU-03).

Entregable 2 - seguridad (RNF-03, RN-02):
antes cualquiera, sin iniciar sesión, podía ver todos los usuarios, crearse como Admin,
editar o borrar cuentas. Ahora esas acciones exigen token con rol Admin.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError

from src.entities.usuario import Usuario
from src.schemas.response_schema import RespuestaAPI
from src.schemas.usuario_schema import UsuarioCreate, UsuarioLogin, UsuarioResponse, UsuarioUpdate
from src.services import usuario as services_usuario
from src.utils.jwt_utils import create_token, decode_jwt

from .deps import SOLO_ADMIN, DbSession

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

MENSAJE_NO_A_SI_MISMO = "No puede desactivarse, quitarse el rol de administrador ni eliminar su propia cuenta"

_token_opcional = HTTPBearer(auto_error=False)


def _es_admin(db, credenciales: Optional[HTTPAuthorizationCredentials]) -> bool:
    """¿El que hace la petición es un administrador activo? (si no mandó token, no lo es)."""
    if not credenciales:
        return False
    try:
        usuario = services_usuario.obtener_por_id(db, UUID(str(decode_jwt(credenciales.credentials)["user_id"])))
    except Exception:
        return False
    return bool(usuario and usuario.activo and (usuario.rol or "").upper() == "ADMIN")


@router.get("/hay-usuarios")
def hay_usuarios(db: DbSession):
    """Lo usa la pantalla de login para saber si debe crear el primer administrador."""
    return {"hay_usuarios": services_usuario.hay_usuarios(db)}


@router.get("", response_model=List[UsuarioResponse], dependencies=[SOLO_ADMIN])
def listar_usuarios(db: DbSession, skip: int = 0, limit: int = 100):
    """HU-03 esc. 3: lista global de usuarios (solo el administrador)."""
    return services_usuario.obtener_todos(db, skip=skip, limit=limit)


@router.get("/{id_usuario}", response_model=UsuarioResponse, dependencies=[SOLO_ADMIN])
def obtener_usuario(db: DbSession, id_usuario: UUID) -> UsuarioResponse:
    db_usuario = services_usuario.obtener_por_id(db, id_usuario)
    if not db_usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El usuario con ID {id_usuario} no existe en la base de datos",
        )
    return db_usuario


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    db: DbSession,
    dato: UsuarioCreate,
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(_token_opcional),
):
    # HU-02: el registro público SIEMPRE crea estudiantes activos.
    # HU-03: solo un Admin con sesión puede crear docentes o admins (y decidir si queda activo).
    # Excepción: si la base está vacía, el primer usuario puede ser el administrador.
    rol, activo = dato.rol, dato.activo
    es_admin = services_usuario.hay_usuarios(db) and _es_admin(db, credenciales)
    if services_usuario.hay_usuarios(db) and not es_admin:
        rol, activo = "Estudiante", True

    try:
        return services_usuario.crear(
            db,
            nombre_usuario=dato.nombre_usuario,
            tipo_documento=dato.tipo_documento,
            documento_identidad=dato.documento_identidad,
            email=str(dato.email),
            contrasena=dato.contrasena,
            rol=rol,
            activo=activo,
            creado_por_admin=es_admin,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{id_usuario}", response_model=UsuarioResponse)
def actualizar_usuario(db: DbSession, id_usuario: UUID, dato: UsuarioUpdate, admin: Usuario = SOLO_ADMIN):
    """HU-03 esc. 2 y 3: editar datos, cambiar rol o desactivar la cuenta."""
    cambios = dato.model_dump(exclude_unset=True)
    # Si el admin se desactiva o se quita el rol a sí mismo, la plataforma se puede quedar sin administrador
    if id_usuario == admin.id_usuario and (cambios.get("activo") is False or cambios.get("rol", "Admin") != "Admin"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MENSAJE_NO_A_SI_MISMO)
    try:
        usuario = services_usuario.actualizar(db, id_usuario, **cambios)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


@router.delete("/{id_usuario}", response_model=RespuestaAPI)
def eliminar_usuario(db: DbSession, id_usuario: UUID, admin: Usuario = SOLO_ADMIN):
    if id_usuario == admin.id_usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MENSAJE_NO_A_SI_MISMO)
    if not services_usuario.obtener_por_id(db, id_usuario):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    try:
        services_usuario.eliminar(db, id_usuario)
    except IntegrityError:
        # Si el usuario ya tiene cursos, pagos o inscripciones no se puede borrar sin perder
        # la trazabilidad; para quitarle el acceso se desactiva (HU-03 esc. 3).
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario tiene registros asociados y no se puede eliminar. Desactívelo para quitarle el acceso",
        )
    return RespuestaAPI(mensaje="Usuario eliminado exitosamente", exito=True)


@router.post("/login")
def login_usuario(db: DbSession, data: UsuarioLogin):
    """HU-01: inicio de sesión con correo (o nombre de usuario) y contraseña."""
    try:
        usuario = services_usuario.login(db, data.nombre_usuario, data.contrasena)
    except services_usuario.CuentaDesactivadaError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # HU-01 esc. 3

    if not usuario:
        # HU-01 esc. 2 y 4: mismo mensaje si el usuario no existe o la contraseña está mal
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    # Entregable 2: el login devuelve el rol y el nombre para que el front no tenga
    # que descargar la lista de todos los usuarios
    return {
        "access_token": create_token(str(usuario.id_usuario)),
        "token_type": "bearer",
        "id_usuario": str(usuario.id_usuario),
        "nombre_usuario": usuario.nombre_usuario,
        "rol": usuario.rol,
    }
