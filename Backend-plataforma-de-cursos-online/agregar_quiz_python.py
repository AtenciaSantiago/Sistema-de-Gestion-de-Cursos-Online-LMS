"""
Agrega al curso "Introducción a Python" (ya cargado en la base) su guía en PDF y un quiz de 2 preguntas,
para que el curso también se pueda terminar y dé certificado. Si algo ya existe, no lo duplica.
Se ejecuta con 3-agregar-quiz-python.bat
"""

from src.database.config import SessionLocal
import src.app  # noqa: F401 - registra todas las tablas
from src.entities.Curso import Curso
from src.entities.Evaluacion import Evaluacion
from src.entities.Leccion import Leccion
from src.entities.Material import Material
from src.entities.pregunta import Pregunta
from src.services import pregunta as servicio_preguntas

URL_PDF = "http://localhost:4200/materiales/guia-variables-python.pdf"
PREGUNTAS = [
    ("OPCION_MULTIPLE", "¿Qué tipo de dato es 3.14 en Python?", ["int", "float", "str"], "float"),
    ("VERDADERO_FALSO", "En Python una variable se crea al asignarle un valor.", [], "Verdadero"),
]

db = SessionLocal()
curso = db.query(Curso).filter(Curso.nombre_curso == "Introducción a Python").first()
if not curso:
    raise SystemExit("No se encontró el curso 'Introducción a Python'.")
leccion = db.query(Leccion).filter(Leccion.id_curso == curso.id_curso).order_by(Leccion.orden).first()
if not leccion:
    raise SystemExit("El curso no tiene lecciones.")
profe = curso.docente
if not profe:
    raise SystemExit("El curso no tiene profesor asignado.")

if not leccion.descripcion_leccion:
    leccion.descripcion_leccion = "Qué es una variable y los tipos básicos: int, float, str y bool."

if not db.query(Material).filter(Material.id_leccion == leccion.id_leccion).first():
    db.add(Material(id_leccion=leccion.id_leccion, titulo_material="Guía de variables y tipos de datos",
                    tipo_material="PDF", URL_archivo=URL_PDF, id_usuario_creacion=profe.id_usuario))
    print("Material PDF agregado.")
else:
    print("La lección ya tenía material: no se agrega otro.")

evaluacion = db.query(Evaluacion).filter(Evaluacion.id_leccion == leccion.id_leccion).first()
if not evaluacion:
    evaluacion = Evaluacion(id_leccion=leccion.id_leccion, nombre_evaluacion="Quiz de variables", porcentaje=100,
                            nota_minima=3.0, id_usuario_creacion=profe.id_usuario)
    db.add(evaluacion)
    print("Evaluación 'Quiz de variables' (100 %) creada.")
else:
    print(f"La lección ya tenía la evaluación '{evaluacion.nombre_evaluacion}': se usa esa.")
db.commit()

if db.query(Pregunta).filter(Pregunta.id_evaluacion == evaluacion.id_evaluacion).count() == 0:
    for tipo, enunciado, opciones, clave in PREGUNTAS:
        servicio_preguntas.crear(db, evaluacion.id_evaluacion, {
            "tipo": tipo, "enunciado": enunciado, "opciones": opciones, "respuesta_correcta": clave,
        }, profe)
    print("2 preguntas agregadas (con la Factory, igual que desde la pantalla).")
else:
    print("La evaluación ya tenía preguntas: no se agregan más.")

db.close()
print("\nListo: el curso 'Introducción a Python' ya se puede terminar y da certificado.")
