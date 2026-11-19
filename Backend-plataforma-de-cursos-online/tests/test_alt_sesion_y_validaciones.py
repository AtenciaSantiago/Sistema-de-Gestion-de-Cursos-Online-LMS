"""
Entregable 3 - Flujos alternativos y excepciones.
Reglas que aplican a todo el sistema: sesión y token, permisos por rol, filtros de consulta, recursos inexistentes y configuración.

Cada prueba cita la historia y el escenario, y afirma el código HTTP, el mensaje exacto y,
cuando aplica, lo que quedó en la base de datos. Las transiciones de la inscripción están en
test_maquina_estados_inscripcion.py y aquí no se repiten.
"""


import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from conftest import token_de
from src.endpoints.deps import MENSAJE_SIN_PERMISO, MENSAJE_SIN_SESION
from src.entities.usuario import Usuario
from src.utils.jwt_utils import ALGORITHM, SECRET_KEY

MENSAJE_FORMATO_INVALIDO = "Hay datos con formato inválido. Revise los campos marcados"  # src/app.py
MENSAJE_TOKEN_INVALIDO = "Token inválido"  # src/endpoints/deps.py
ID_INEXISTENTE = "00000000-0000-0000-0000-000000000000"
RAIZ_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ------------------------------ Ayudas ------------------------------------


# =============================== RF-07 / filtros =========================
def test_historial_con_fecha_inicial_mayor_que_la_final(cliente, escenario):
    """RF-07: en el historial la fecha inicial no puede ser mayor que la final."""
    r = cliente.get("/historial", headers=token_de(escenario["admin"]),
                    params={"desde": "2026-11-10", "hasta": "2026-11-01"})
    assert r.status_code == 400
    assert r.json()["detail"] == "La fecha inicial no puede ser mayor que la fecha final"


@pytest.mark.parametrize("ruta, mensaje", [
    ("/pago?desde=2026-10-10&hasta=2026-10-01", "La fecha inicial no puede ser posterior a la fecha final"),
    ("/inscripciones?estado=PERDIDA",
     "Estado no válido. Use uno de: PENDIENTE, ACTIVA, FINALIZADA, CANCELADA, APROBADA, REPROBADA"),
    ("/inscripciones/cierres?estado=ACTIVA", "El filtro de cierres debe ser APROBADA, REPROBADA o FINALIZADA"),
    ("/historial?entidad=FACTURA", "La entidad debe ser una de: CURSO, LECCION, MATERIAL, EVALUACION, PREGUNTA, CATEGORIA"),
], ids=["pagos_fechas", "inscripciones_estado", "cierres_estado", "historial_entidad"])
def test_filtros_invalidos_mensaje_exacto(cliente, escenario, ruta, mensaje):
    """Auditorías del administrador (RF-07, RF-10, HU-17): cada filtro inválido responde 400 con su mensaje exacto."""
    r = cliente.get(ruta, headers=token_de(escenario["admin"]))
    assert r.status_code == 400
    assert r.json()["detail"] == mensaje


# =============================== Sesión y permisos =======================
@pytest.mark.parametrize("metodo, ruta", [
    ("get", "/usuarios"),
    ("get", "/mis-cursos"),
    ("post", "/cursos"),
    ("get", "/inscripciones/cierres"),
])
def test_peticion_sin_token_responde_401_en_espanol(cliente, metodo, ruta):
    """Entregable 3: sin el encabezado Authorization la API responde 401 con un mensaje en español."""
    r = getattr(cliente, metodo)(ruta)

    assert r.status_code == 401
    assert r.json()["detail"] == MENSAJE_SIN_SESION == "Debe iniciar sesión para realizar esta acción"
    assert r.headers["www-authenticate"] == "Bearer"


def test_rol_no_permitido_mensaje_exacto(cliente, escenario):
    """RN-02: un estudiante en una ruta administrativa recibe 403 con el mensaje exacto."""
    r = cliente.get("/usuarios", headers=token_de(escenario["estudiante"]))
    assert r.status_code == 403
    assert r.json()["detail"] == MENSAJE_SIN_PERMISO


def _token(carga):
    return {"Authorization": "Bearer " + jwt.encode(carga, SECRET_KEY, algorithm=ALGORITHM)}


def test_token_vencido_responde_401(cliente, escenario):
    """RNF-03: un token bien firmado pero vencido (la sesión dura 2 horas) ya no da acceso."""
    estudiante = escenario["estudiante"]
    vencido = _token({"user_id": str(estudiante.id_usuario), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)})
    vigente = _token({"user_id": str(estudiante.id_usuario), "exp": datetime.now(timezone.utc) + timedelta(minutes=1)})

    r = cliente.get("/mis-cursos", headers=vencido)

    assert r.status_code == 401
    assert r.json()["detail"] == MENSAJE_TOKEN_INVALIDO
    assert cliente.get("/mis-cursos", headers=vigente).status_code == 200  # la única diferencia es la fecha


@pytest.mark.parametrize("caso", ["firma_falsa", "texto_cualquiera", "sin_user_id", "usuario_inexistente", "id_que_no_es_uuid"])
def test_token_invalido_mensaje_exacto(cliente, escenario, caso):
    """RNF-03: cualquier token que no identifique a un usuario activo responde 401 «Token inválido»."""
    futuro = datetime.now(timezone.utc) + timedelta(hours=1)
    id_estudiante = str(escenario["estudiante"].id_usuario)
    if caso == "firma_falsa":
        otra_clave = "otra-clave-que-no-es-la-del-servidor-0123456789"
        token = jwt.encode({"user_id": id_estudiante, "exp": futuro}, otra_clave, algorithm=ALGORITHM)
        encabezado = {"Authorization": f"Bearer {token}"}
    elif caso == "texto_cualquiera":
        encabezado = {"Authorization": "Bearer token-falso"}
    elif caso == "sin_user_id":
        encabezado = _token({"exp": futuro})
    elif caso == "usuario_inexistente":
        encabezado = _token({"user_id": str(uuid.uuid4()), "exp": futuro})
    else:
        encabezado = _token({"user_id": "no-es-un-uuid", "exp": futuro})
    r = cliente.get("/mis-cursos", headers=encabezado)
    assert r.status_code == 401
    assert r.json()["detail"] == MENSAJE_TOKEN_INVALIDO


# =============================== Transversales ===========================
def test_identificador_mal_escrito_en_la_ruta_responde_422(cliente, escenario):
    """Datos de entrada (transversal): un id que no es UUID -> 422 con el mensaje de formato y el campo marcado."""
    r = cliente.get("/usuarios/no-es-un-uuid", headers=token_de(escenario["admin"]))
    assert r.status_code == 422
    assert r.json()["detail"] == MENSAJE_FORMATO_INVALIDO
    assert r.json()["campos"] == ["id_usuario"]


def test_rol_desconocido_al_crear_un_usuario_responde_422(cliente, db, escenario):
    """Datos de entrada (transversal): el rol debe ser Admin, Docente o Estudiante."""
    r = cliente.post("/usuarios", headers=token_de(escenario["admin"]), json={
        "nombre_usuario": "Pedro Gil", "tipo_documento": "CC", "documento_identidad": "500",
        "email": "pedro@email.com", "contrasena": "Clave123*", "rol": "Jefe",
    })
    assert r.status_code == 422
    assert r.json()["detail"] == MENSAJE_FORMATO_INVALIDO
    assert r.json()["campos"] == ["rol"]
    assert "El rol debe ser Admin, Docente o Estudiante" in r.json()["errores"][0]["msg"]
    assert db.query(Usuario).filter(Usuario.email == "pedro@email.com").count() == 0


@pytest.mark.parametrize("metodo, ruta, mensaje", [
    # Tal como es HOY: al consultar un usuario el texto es distinto al de editarlo (src/endpoints/usuario.py:60)
    ("get", "/usuarios/{id}", f"El usuario con ID {ID_INEXISTENTE} no existe en la base de datos"),
    ("put", "/usuarios/{id}", "Usuario no encontrado"),
    ("get", "/categorias/{id}", "Categoría no encontrada"),
    ("get", "/cursos/{id}", "Curso no encontrado"),
    ("get", "/lecciones/{id}", "Lección no encontrada"),
    ("get", "/material/{id}", "Material no encontrado"),
    ("get", "/evaluaciones/{id}", "Evaluación no encontrada"),
    ("put", "/preguntas/{id}", "Pregunta no encontrada"),
    ("get", "/inscripciones/{id}", "Inscripción no encontrada"),
    ("get", "/pago/{id}", "Pago no encontrado"),
    ("get", "/certificados/{id}", "Certificado no encontrado"),
], ids=["usuario_consultar", "usuario_editar", "categoria", "curso", "leccion", "material", "evaluacion",
        "pregunta", "inscripcion", "pago", "certificado"])
def test_recurso_inexistente_responde_404(cliente, escenario, metodo, ruta, mensaje):
    """Recurso inexistente (transversal): consultar o editar un id que no existe responde 404 con su mensaje."""
    url = ruta.format(id=ID_INEXISTENTE)
    admin = token_de(escenario["admin"])
    r = cliente.put(url, headers=admin, json={}) if metodo == "put" else cliente.get(url, headers=admin)
    assert r.status_code == 404
    assert r.json()["detail"] == mensaje


def test_completar_una_leccion_que_no_existe_responde_404(cliente, escenario):
    """Recurso inexistente (HU-12): marcar como completada una lección que no existe responde 404."""
    r = cliente.post(f"/mis-cursos/lecciones/{ID_INEXISTENTE}/completar", headers=token_de(escenario["estudiante"]))
    assert r.status_code == 404
    assert r.json()["detail"] == "La lección no existe"


@pytest.mark.parametrize("variable, modulo, mensaje", [
    ("SECRET_KEY", "src.utils.jwt_utils", "Se requiere SECRET_KEY en el archivo .env"),
    ("DATABASE_URL", "src.database.config", "Se requiere DATABASE_URL en el archivo .env"),
])
def test_sin_configuracion_la_aplicacion_no_arranca(variable, modulo, mensaje):
    """Arranque (transversal): sin SECRET_KEY o sin DATABASE_URL el módulo falla al cargarse, con un mensaje claro."""
    entorno = dict(os.environ, **{variable: ""})  # vacía: load_dotenv no la pisa y el código la toma como ausente
    proceso = subprocess.run([sys.executable, "-c", f"import {modulo}"], cwd=RAIZ_BACKEND, env=entorno,
                             capture_output=True, text=True, timeout=60)
    assert proceso.returncode != 0
    assert f"ValueError: {mensaje}" in proceso.stderr
