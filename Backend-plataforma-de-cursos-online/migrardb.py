"""
Script para crear o actualizar las tablas en Neon (PostgreSQL).
Ejecutar después de configurar DATABASE_URL en .env (se puede correr varias veces):

  python migrardb.py

No es necesario levantar la API; este script solo aplica el esquema.
"""

import os

from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError

import src.entities.categoria  # noqa: F401 - registrar modelo
import src.entities.usuario # noqa: F401 - registrar modelo
import src.entities.Curso # noqa: F401 - registrar modelo
import src.entities.inscripcion # noqa: F401 - registrar modelo
import src.entities.Pago # noqa: F401 - registrar modelo
import src.entities.Leccion # noqa: F401 - registrar modelo
import src.entities.Material # noqa: F401 - registrar modelo
import src.entities.Evaluacion # noqa: F401 - registrar modelo
import src.entities.calificacion # noqa: F401 - registrar modelo
import src.entities.certificado # noqa: F401 - registrar modelo
import src.entities.pregunta # noqa: F401 - Entregable 2: preguntas de evaluación (Factory Method)
import src.entities.progreso_leccion # noqa: F401 - Entregable 2: progreso por lección (HU-12)
import src.entities.registro_cierre # noqa: F401 - Entregable 2: auditoría de cierres (Observer)
import src.entities.intento_evaluacion # noqa: F401 - Entregable 2: intentos de cada evaluación (RF-13)
import src.entities.historial_cambio # noqa: F401 - Entregable 2: historial de cambios de contenidos (RF-07)

from sqlalchemy import inspect, text

from src.database.config import create_tables, engine


# Columnas nuevas del Entregable 2: (tabla, columna, definición SQL)
COLUMNAS_NUEVAS = [
    ("evaluacion", "nota_minima", "FLOAT NOT NULL DEFAULT 3.0"),  # HU-14
    ("curso", "precio", "FLOAT NOT NULL DEFAULT 0"),  # HU-09
    ("pago", "referencia", "VARCHAR(50)"),  # HU-09
    ("certificado", "codigo_verificacion", "VARCHAR(30) UNIQUE"),  # HU-13
    ("certificado", "promedio_final", "FLOAT"),  # HU-13
    ("curso", "id_docente", "UUID REFERENCES usuario(id_usuario)"),  # HU-04 / HU-05: profesor asignado
]


def aplicar_cambios_entregable_2():
    """
    create_tables() crea tablas nuevas, pero NO agrega columnas a tablas que ya existen.
    Por eso agregamos a mano las columnas nuevas si todavía no están.
    """
    for tabla, columna, definicion in COLUMNAS_NUEVAS:
        columnas = [c["name"] for c in inspect(engine).get_columns(tabla)]
        if columna not in columnas:
            with engine.begin() as conexion:
                conexion.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"))
            print(f"Columna {tabla}.{columna} agregada.")

    # Cursos viejos: el profesor asignado es quien creó el curso (si era Docente)
    with engine.begin() as conexion:
        conexion.execute(text(
            "UPDATE curso SET id_docente = id_usuario_creacion "
            "WHERE id_docente IS NULL AND id_usuario_creacion IN "
            "(SELECT id_usuario FROM usuario WHERE UPPER(rol) = 'DOCENTE')"
        ))
        # Cursos viejos con estado "ACTIVO" pasan al estado del E1: PUBLICADO
        conexion.execute(text("UPDATE curso SET estado_curso = 'PUBLICADO' WHERE UPPER(estado_curso) = 'ACTIVO'"))
        # HU-05 esc. 3: un curso publicado debe tener información completa, profesor y al menos una
        # lección. Los viejos que no cumplan vuelven a BORRADOR (los ya matriculados no se afectan).
        ocultados = conexion.execute(text(
            "UPDATE curso SET estado_curso = 'BORRADOR' "
            "WHERE estado_curso = 'PUBLICADO' AND ("
            "  id_docente IS NULL OR descripcion_curso IS NULL OR TRIM(descripcion_curso) = '' "
            "  OR NOT EXISTS (SELECT 1 FROM leccion WHERE leccion.id_curso = curso.id_curso))"
        )).rowcount
        if ocultados:
            print(f"{ocultados} curso(s) pasaron a BORRADOR por no cumplir la HU-05 (falta profesor, descripción o lecciones).")

    # Arreglos de tablas que ya existían (solo aplica en PostgreSQL / Neon)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conexion:
            for sentencia in ARREGLOS_POSTGRES:
                conexion.execute(text(sentencia))
        print("Arreglos de longitud de títulos y orden de lecciones aplicados.")


ARREGLOS_POSTGRES = [
    # Los títulos solo aceptaban 20 caracteres
    "ALTER TABLE leccion ALTER COLUMN titulo_leccion TYPE VARCHAR(150)",
    "ALTER TABLE material ALTER COLUMN titulo_material TYPE VARCHAR(150)",
    "ALTER TABLE evaluacion ALTER COLUMN nombre_evaluacion TYPE VARCHAR(150)",
    # El orden era único en TODA la base; ahora es único dentro de cada curso
    "ALTER TABLE leccion DROP CONSTRAINT IF EXISTS leccion_orden_key",
    """DO $$ BEGIN
         IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_leccion_curso_orden') THEN
           ALTER TABLE leccion ADD CONSTRAINT uq_leccion_curso_orden UNIQUE (id_curso, orden);
         END IF;
       END $$""",
    # Entregable 2: una inscripción por estudiante y curso; un certificado por inscripción.
    # Si la base vieja ya tuviera duplicados no se detiene la migración: solo avisa.
    """DO $$ BEGIN
         IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_inscripcion_curso_estudiante') THEN
           ALTER TABLE inscripcion ADD CONSTRAINT uq_inscripcion_curso_estudiante UNIQUE (id_curso, id_usuario_inscrito);
         END IF;
       EXCEPTION WHEN unique_violation THEN
         RAISE NOTICE 'Hay inscripciones repetidas: revíselas antes de activar la restricción';
       END $$""",
    """DO $$ BEGIN
         IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_certificado_inscripcion') THEN
           ALTER TABLE certificado ADD CONSTRAINT uq_certificado_inscripcion UNIQUE (id_inscripcion);
         END IF;
       EXCEPTION WHEN unique_violation THEN
         RAISE NOTICE 'Hay certificados repetidos: revíselos antes de activar la restricción';
       END $$""",
]

# Cargar .env desde la carpeta del proyecto (donde está migrardb.py)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


try:
    create_tables()
    aplicar_cambios_entregable_2()
    print("Tablas creadas y actualizadas correctamente en la base de datos.")
except OperationalError as e:
    if "password authentication failed" in str(e).lower():
        print("Error: Neon rechazó la contraseña (password authentication failed).")
        print(
            "  - Entra a https://console.neon.tech y revisa la conexión del proyecto."
        )
        print(
            "  - Copia de nuevo la connection string (Connection string) y actualiza .env."
        )
        print(
            "  - Si la contraseña tiene caracteres especiales (& # @ ?), codifícala en URL (ej. @ → %40)."
        )
    else:
        print("Error de conexión a la base de datos:", e)
    raise SystemExit(1)