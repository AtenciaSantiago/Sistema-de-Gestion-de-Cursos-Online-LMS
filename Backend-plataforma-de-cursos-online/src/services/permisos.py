"""
Quién puede modificar qué (RN-02).

- El Admin puede gestionar todos los cursos.
- El Docente solo los cursos donde es el profesor asignado (o los que él creó).
- El contenido (lecciones, materiales, evaluaciones y preguntas) sigue la misma regla
  que su curso, porque todo cuelga de un curso (RN-03).

Así un docente no puede cambiar ni borrar el curso de otro docente.
"""

from sqlalchemy.orm import Session

from src.entities.Curso import Curso
from src.entities.Evaluacion import Evaluacion
from src.entities.Leccion import Leccion
from src.entities.usuario import Usuario

MENSAJE_NO_ES_SU_CURSO = "No tiene permisos para modificar este curso"


def es_admin(usuario: Usuario) -> bool:
    return (usuario.rol or "").upper() == "ADMIN"


def puede_gestionar_curso(usuario: Usuario, curso: Curso) -> bool:
    if es_admin(usuario):
        return True
    # El docente gestiona solo el curso que tiene ASIGNADO. Si el admin se lo pasa a otro
    # profesor, el anterior deja de poder tocarlo aunque haya sido quien lo creó.
    return curso is not None and curso.id_docente == usuario.id_usuario


def exigir_gestion_curso(usuario: Usuario, curso: Curso) -> None:
    if not puede_gestionar_curso(usuario, curso):
        raise PermissionError(MENSAJE_NO_ES_SU_CURSO)


def curso_de_leccion(db: Session, leccion: Leccion) -> Curso:
    return db.query(Curso).filter(Curso.id_curso == leccion.id_curso).first()


def curso_de_evaluacion(db: Session, evaluacion: Evaluacion) -> Curso:
    leccion = db.query(Leccion).filter(Leccion.id_leccion == evaluacion.id_leccion).first()
    return curso_de_leccion(db, leccion)
