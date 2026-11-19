"""
Entregable 3 - Flujos alternativos y excepciones.
EP-01 Autenticación y cuentas: registro público (HU-02) y administración de cuentas y roles (HU-03).

Cada prueba cita la historia y el escenario, y afirma el código HTTP, el mensaje exacto y,
cuando aplica, lo que quedó en la base de datos. Las transiciones de la inscripción están en
test_maquina_estados_inscripcion.py y aquí no se repiten.
"""


import pytest

from conftest import token_de
from src.database.config import engine
from src.endpoints.usuario import MENSAJE_NO_A_SI_MISMO
from src.entities.usuario import Usuario
from src.services.usuario import MENSAJE_CUENTA_DESACTIVADA

MENSAJE_FORMATO_INVALIDO = "Hay datos con formato inválido. Revise los campos marcados"  # src/app.py
MENSAJE_TOKEN_INVALIDO = "Token inválido"  # src/endpoints/deps.py


# ------------------------------ Ayudas ------------------------------------


# =============================== HU-02 ===================================
def test_registro_solo_con_correo_mal_escrito_da_el_mensaje_de_formato(cliente, db, escenario):
    """HU-02 esc. 3: todos los campos llenos pero el correo con formato inválido -> 422 y el campo marcado."""
    r = cliente.post("/usuarios", json={
        "nombre_usuario": "Pedro Gil", "tipo_documento": "CC", "documento_identidad": "500",
        "email": "pedro@", "contrasena": "Clave123*",
    })
    assert r.status_code == 422
    assert r.json()["detail"] == MENSAJE_FORMATO_INVALIDO
    assert r.json()["campos"] == ["email"]
    assert db.query(Usuario).filter(Usuario.nombre_usuario == "Pedro Gil").count() == 0


def test_registro_con_documento_repetido(cliente, db, escenario):
    """HU-02 (ajuste E2): el documento de identidad no se puede repetir."""
    r = cliente.post("/usuarios", json={
        "nombre_usuario": "Pedro Gil", "tipo_documento": "CC", "documento_identidad": "300",  # el de Lucía
        "email": "pedro@email.com", "contrasena": "Clave123*",
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "El número de documento ya se encuentra registrado en la plataforma"
    assert db.query(Usuario).filter(Usuario.email == "pedro@email.com").count() == 0


def test_registro_con_nombre_de_usuario_repetido(cliente, db, escenario):
    """HU-02 (ajuste E2): el nombre de usuario no se puede repetir."""
    r = cliente.post("/usuarios", json={
        "nombre_usuario": "Lucía Martínez", "tipo_documento": "CC", "documento_identidad": "500",
        "email": "otra.lucia@email.com", "contrasena": "Clave123*",
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "El nombre de usuario ya existe"
    assert db.query(Usuario).filter(Usuario.email == "otra.lucia@email.com").count() == 0


# =============================== HU-03 ===================================
def test_admin_cambia_el_rol_y_el_permiso_aplica_de_inmediato(cliente, db, escenario):
    """HU-03 esc. 2: el administrador pasa a Lucía de Estudiante a Docente y ella ya entra a la gestión de cursos."""
    lucia = escenario["estudiante"]
    token = token_de(lucia)
    assert cliente.get("/cursos", headers=token).status_code == 403  # antes, como estudiante, no entra

    r = cliente.put(f"/usuarios/{lucia.id_usuario}", headers=token_de(escenario["admin"]), json={"rol": "Docente"})

    assert r.status_code == 200, r.text
    assert r.json()["rol"] == "Docente"
    db.refresh(lucia)
    assert lucia.rol == "Docente"
    assert cliente.get("/cursos", headers=token).status_code == 200  # con el mismo token
    assert cliente.get("/mis-cursos", headers=token).status_code == 403  # y deja de ser estudiante


def test_admin_desactiva_por_la_api_y_el_usuario_pierde_el_acceso(cliente, db, escenario):
    """HU-03 esc. 3: la desactivación hecha por PUT /usuarios quita el acceso (token viejo e inicio de sesión)."""
    lucia = escenario["estudiante"]
    token = token_de(lucia)
    assert cliente.get("/mis-cursos", headers=token).status_code == 200

    r = cliente.put(f"/usuarios/{lucia.id_usuario}", headers=token_de(escenario["admin"]), json={"activo": False})

    assert r.status_code == 200, r.text
    assert r.json()["activo"] is False
    db.refresh(lucia)
    assert lucia.activo is False
    con_token_viejo = cliente.get("/mis-cursos", headers=token)
    assert con_token_viejo.status_code == 401 and con_token_viejo.json()["detail"] == MENSAJE_TOKEN_INVALIDO
    login = cliente.post("/usuarios/login", json={"nombre_usuario": "lucia.martinez@email.com", "contrasena": "Clave123*"})
    assert login.status_code == 403 and login.json()["detail"] == MENSAJE_CUENTA_DESACTIVADA


@pytest.mark.parametrize("accion", ["desactivarse", "quitarse_el_rol", "eliminarse"])
def test_el_admin_no_se_bloquea_a_si_mismo_mensaje_exacto(cliente, db, escenario, accion):
    """HU-03 (regla del E2): el mensaje exacto cuando el administrador intenta dejar la plataforma sin administrador."""
    admin = escenario["admin"]
    url = f"/usuarios/{admin.id_usuario}"
    if accion == "desactivarse":
        r = cliente.put(url, headers=token_de(admin), json={"activo": False})
    elif accion == "quitarse_el_rol":
        r = cliente.put(url, headers=token_de(admin), json={"rol": "Estudiante"})
    else:
        r = cliente.delete(url, headers=token_de(admin))
    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_NO_A_SI_MISMO
    db.refresh(admin)
    assert admin.activo is True and admin.rol == "Admin"


@pytest.mark.skipif(engine.dialect.name == "sqlite",
                    reason="SQLite no hace cumplir las llaves foráneas: solo se puede verificar contra PostgreSQL")
def test_no_se_elimina_un_usuario_con_registros_asociados(cliente, db, escenario):
    """Integridad (HU-03): un docente con cursos no se borra; se responde 400 y se sugiere desactivarlo."""
    docente = escenario["docente"]
    r = cliente.delete(f"/usuarios/{docente.id_usuario}", headers=token_de(escenario["admin"]))
    assert r.status_code == 400
    assert r.json()["detail"] == (
        "El usuario tiene registros asociados y no se puede eliminar. Desactívelo para quitarle el acceso"
    )
    db.expire_all()
    assert db.query(Usuario).filter(Usuario.id_usuario == docente.id_usuario).count() == 1
