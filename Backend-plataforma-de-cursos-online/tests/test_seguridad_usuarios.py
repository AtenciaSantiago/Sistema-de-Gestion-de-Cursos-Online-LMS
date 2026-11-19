"""
Pruebas de seguridad de usuarios y login (HU-01, HU-02, RNF-03).
"""

from conftest import token_de

NUEVO = {
    "nombre_usuario": "pirata",
    "tipo_documento": "CC",
    "documento_identidad": "999",
    "email": "pirata@email.com",
    "contrasena": "Clave123*",
    "rol": "Admin",
    "activo": True,
}


def test_login_con_contrasena_correcta_devuelve_token_y_rol(cliente, escenario):
    r = cliente.post("/usuarios/login", json={"nombre_usuario": "Lucía Martínez", "contrasena": "Clave123*"})
    assert r.status_code == 200
    assert r.json()["rol"] == "Estudiante"
    assert r.json()["access_token"]


def test_login_con_contrasena_incorrecta_se_rechaza(cliente, escenario):
    r = cliente.post("/usuarios/login", json={"nombre_usuario": "Lucía Martínez", "contrasena": "otra"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Credenciales inválidas"


def test_registro_publico_siempre_crea_estudiante(cliente, escenario):
    r = cliente.post("/usuarios", json=NUEVO)  # intenta registrarse como Admin sin sesión
    assert r.status_code == 201
    assert r.json()["rol"] == "Estudiante"


def test_admin_con_sesion_si_puede_crear_docentes(cliente, escenario):
    r = cliente.post("/usuarios", headers=token_de(escenario["admin"]), json=dict(NUEVO, rol="Docente"))
    assert r.json()["rol"] == "Docente"


def test_el_primer_usuario_puede_ser_admin(cliente, db):
    r = cliente.post("/usuarios", json=NUEVO)
    assert r.json()["rol"] == "Admin"


def test_listar_usuarios_exige_sesion(cliente, escenario):
    assert cliente.get("/usuarios").status_code in (401, 403)
    assert cliente.get("/usuarios", headers=token_de(escenario["admin"])).status_code == 200


def test_solo_admin_edita_o_borra_usuarios(cliente, escenario):
    id_lucia = escenario["estudiante"].id_usuario
    assert cliente.put(f"/usuarios/{id_lucia}", json={"rol": "Admin"}).status_code in (401, 403)
    assert cliente.put(f"/usuarios/{id_lucia}", headers=token_de(escenario["estudiante"]), json={"rol": "Admin"}).status_code == 403
    assert cliente.delete(f"/usuarios/{id_lucia}", headers=token_de(escenario["docente"])).status_code == 403


def test_hay_usuarios_es_publico(cliente, escenario):
    assert cliente.get("/usuarios/hay-usuarios").json() == {"hay_usuarios": True}
