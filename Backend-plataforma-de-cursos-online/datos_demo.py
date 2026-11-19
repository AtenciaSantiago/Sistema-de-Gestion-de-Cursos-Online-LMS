"""
Carga datos de demostración para la sustentación (Entregable 2).

Usa los mismos datos del prototipo Figma del Entregable 1:
- Docente: Ana Torres
- Docente sin cursos: Carlos Ruiz (para mostrar el mensaje de la HU-07 esc. 2)
- Estudiante: Lucía Martínez (todavía SIN inscribir, para mostrar la compra)
- Curso: "Diseño de interfaces con Figma" (US$ 120) con 3 lecciones y 3 evaluaciones
  (20 %, 30 % y 50 %, igual que en el Figma)
- Curso: "Introducción a Python" (US$ 90) con 1 lección y su evaluación (100 %)

Ejecutar (con la base de datos vacía o nueva):
    python datos_demo.py

Usuarios para entrar (contraseña de todos: Clave123*):
    admin · Ana Torres · Carlos Ruiz · Lucía Martínez
"""

from src.database.config import Base, SessionLocal, engine
import src.app  # noqa: F401 - registra todos los modelos
from src.entities.Curso import Curso
from src.entities.Evaluacion import Evaluacion
from src.entities.Leccion import Leccion
from src.entities.Material import Material
from src.entities.categoria import Categoria
from src.entities.usuario import Usuario
from src.services import pregunta as servicio_preguntas
from src.services.usuario import _hash_contrasena

CLAVE = "Clave123*"


def usuario(db, nombre, email, documento, rol):
    u = Usuario(nombre_usuario=nombre, tipo_documento="CC", documento_identidad=documento,
                email=email, contrasena=_hash_contrasena(CLAVE), rol=rol, activo=True)
    db.add(u)
    db.commit()
    return u


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(Usuario).first():
        print("La base ya tiene datos; no se cargó nada.")
        return

    admin = usuario(db, "admin", "admin@campusdigital.co", "1000000001", "Admin")
    ana = usuario(db, "Ana Torres", "ana.torres@campusdigital.co", "1000000002", "Docente")
    usuario(db, "Carlos Ruiz", "carlos.ruiz@campusdigital.co", "1000000003", "Docente")
    usuario(db, "Lucía Martínez", "lucia.martinez@email.com", "1020304050", "Estudiante")

    diseno = Categoria(nombre_categoria="Diseño digital", id_usuario_creacion=admin.id_usuario)
    progra = Categoria(nombre_categoria="Programación", id_usuario_creacion=admin.id_usuario)
    db.add_all([diseno, progra])
    db.commit()

    figma = Curso(id_categoria=diseno.id_categoria, nombre_curso="Diseño de interfaces con Figma",
                  descripcion_curso="De tu primera idea a un prototipo: diseña experiencias digitales claras y usables.",
                  duracion_horas=12, estado_curso="PUBLICADO", precio=120.0, id_docente=ana.id_usuario,
                  id_usuario_creacion=ana.id_usuario)
    python = Curso(id_categoria=progra.id_categoria, nombre_curso="Introducción a Python",
                   descripcion_curso="Variables, funciones y estructuras de datos desde cero.",
                   duracion_horas=20, estado_curso="PUBLICADO", precio=90.0, id_docente=ana.id_usuario,
                   id_usuario_creacion=ana.id_usuario)
    borrador = Curso(id_categoria=progra.id_categoria, nombre_curso="APIs con FastAPI (próximamente)",
                     descripcion_curso="Curso en preparación.", duracion_horas=16, estado_curso="BORRADOR",
                     precio=150.0, id_docente=ana.id_usuario, id_usuario_creacion=ana.id_usuario)
    db.add_all([figma, python, borrador])
    db.commit()

    plan = [
        ("Introducción al diseño de interfaces", "Qué es una interfaz, usuarios y objetivos.",
         "Guía de jerarquía visual", "Cuestionario de fundamentos", 20, [
             ("OPCION_MULTIPLE", "¿Qué principio ayuda a guiar la mirada del usuario?",
              ["Jerarquía visual", "Colores aleatorios", "Texto muy pequeño"], "Jerarquía visual"),
             ("VERDADERO_FALSO", "El contraste ayuda a destacar la acción principal.", [], "Verdadero"),
         ]),
        ("Componentes y estilos", "Crear componentes reutilizables y estilos de texto y color.",
         "Plantilla de práctica", "Práctica de componentes", 30, [
             ("OPCION_MULTIPLE", "¿Para qué sirve un componente en Figma?",
              ["Reutilizar elementos", "Borrar capas", "Exportar PDF"], "Reutilizar elementos"),
             ("VERDADERO_FALSO", "Cambiar el componente principal actualiza sus copias.", [], "Verdadero"),
         ]),
        ("Prototipado y navegación", "Conectar pantallas y probar el flujo con usuarios.",
         "Checklist de prototipo", "Proyecto final de interfaz", 50, [
             ("OPCION_MULTIPLE", "¿Qué se prueba con un prototipo navegable?",
              ["El flujo del usuario", "La base de datos", "El servidor"], "El flujo del usuario"),
             ("VERDADERO_FALSO", "Un prototipo debe probarse con usuarios reales.", [], "Verdadero"),
         ]),
    ]
    for orden, (titulo, descripcion, material, evaluacion, porcentaje, preguntas) in enumerate(plan, start=1):
        leccion = Leccion(id_curso=figma.id_curso, titulo_leccion=titulo, descripcion_leccion=descripcion,
                          orden=orden, duracion_horas=4, id_usuario_creacion=ana.id_usuario)
        db.add(leccion)
        db.commit()
        db.add(Material(id_leccion=leccion.id_leccion, titulo_material=material, tipo_material="PDF",
                        URL_archivo="https://www.figma.com/resource-library/", id_usuario_creacion=ana.id_usuario))
        ev = Evaluacion(id_leccion=leccion.id_leccion, nombre_evaluacion=evaluacion, porcentaje=porcentaje,
                        nota_minima=3.0, id_usuario_creacion=ana.id_usuario)
        db.add(ev)
        db.commit()
        for tipo, enunciado, opciones, clave in preguntas:
            # Se crean con la Factory, igual que cuando el docente las agrega desde la pantalla
            servicio_preguntas.crear(db, ev.id_evaluacion, {
                "tipo": tipo, "enunciado": enunciado, "opciones": opciones, "respuesta_correcta": clave,
            }, ana)

    # Curso de Python: una lección con su material y su evaluación (100 %), para que también se pueda terminar
    leccion_py = Leccion(id_curso=python.id_curso, titulo_leccion="Variables y tipos de datos",
                         descripcion_leccion="Qué es una variable y los tipos básicos: int, float, str y bool.",
                         orden=1, duracion_horas=5, id_usuario_creacion=ana.id_usuario)
    db.add(leccion_py)
    db.commit()
    # El PDF lo sirve la página (carpeta public/materiales del frontend)
    db.add(Material(id_leccion=leccion_py.id_leccion, titulo_material="Guía de variables y tipos de datos", tipo_material="PDF",
                    URL_archivo="http://localhost:4200/materiales/guia-variables-python.pdf", id_usuario_creacion=ana.id_usuario))
    ev_py = Evaluacion(id_leccion=leccion_py.id_leccion, nombre_evaluacion="Quiz de variables", porcentaje=100,
                       nota_minima=3.0, id_usuario_creacion=ana.id_usuario)
    db.add(ev_py)
    db.commit()
    for tipo, enunciado, opciones, clave in [
        ("OPCION_MULTIPLE", "¿Qué tipo de dato es 3.14 en Python?", ["int", "float", "str"], "float"),
        ("VERDADERO_FALSO", "En Python una variable se crea al asignarle un valor.", [], "Verdadero"),
    ]:
        servicio_preguntas.crear(db, ev_py.id_evaluacion, {
            "tipo": tipo, "enunciado": enunciado, "opciones": opciones, "respuesta_correcta": clave,
        }, ana)
    print("Datos de demostración cargados. Contraseña de todos los usuarios:", CLAVE)


if __name__ == "__main__":
    main()
