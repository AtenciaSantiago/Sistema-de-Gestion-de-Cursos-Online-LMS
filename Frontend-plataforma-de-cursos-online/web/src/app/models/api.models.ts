// Modelos de lo que entra y sale de la API (iguales a los esquemas de src/schemas del backend).
// Entregable 2: quién crea o edita un registro ya NO se manda desde aquí; el backend lo saca del token.

// =========================== Usuarios (HU-01, HU-02, HU-03) ===========================
export type Rol = 'Admin' | 'Docente' | 'Estudiante';

export interface UsuarioResponse {
  id_usuario: string;
  nombre_usuario: string;
  tipo_documento: string;
  documento_identidad: string;
  email: string;
  rol: Rol;
  activo: boolean;
  fecha_creacion: string;
  fecha_edicion: string | null;
}

export interface UsuarioCreate {
  nombre_usuario: string;
  tipo_documento: string;
  documento_identidad: string;
  email: string;
  contrasena: string;
  rol: Rol;
  activo: boolean;
}

export type UsuarioUpdate = Partial<UsuarioCreate>;

export interface LoginResponse {
  access_token: string;
  token_type: string;
  id_usuario: string;
  nombre_usuario: string;
  rol: Rol;
}

// =========================== Categorías y cursos (HU-04 a HU-07, HU-10) ===========================
export interface CategoriaResponse {
  id_categoria: string;
  nombre_categoria: string;
  fecha_creacion: string;
  fecha_edicion: string | null;
}

export interface CategoriaCreate {
  nombre_categoria: string;
}

export type EstadoCurso = 'BORRADOR' | 'PUBLICADO';

export interface CursoResponse {
  id_curso: string;
  id_categoria: string;
  nombre_categoria: string | null;
  nombre_curso: string;
  duracion_horas: number;
  estado_curso: EstadoCurso;
  descripcion_curso: string | null;
  precio: number | null;
  id_docente: string | null;
  nombre_docente: string | null;
  numero_lecciones: number; // HU-07 esc. 1
  fecha_creacion: string;
  fecha_edicion: string | null;
}

/** HU-04: todo curso nuevo nace en BORRADOR, por eso aquí no va el estado. */
export interface CursoCreate {
  id_categoria: string;
  nombre_curso: string;
  descripcion_curso: string;
  duracion_horas: number;
  precio: number;
  id_docente?: string | null; // solo lo escoge el Admin
}

export interface CursoUpdate extends Partial<CursoCreate> {
  estado_curso?: EstadoCurso; // HU-05: solo el Admin
}

/** HU-10: estudiantes matriculados en un curso del docente. */
export interface EstudianteMatriculado {
  id_estudiante: string;
  nombre_estudiante: string;
  email: string;
  fecha_inscripcion: string;
  porcentaje_avance: number;
  estado_inscripcion: 'ACTIVA' | 'APROBADA' | 'REPROBADA';
}

export interface ReporteEstudiantes {
  id_curso: string;
  nombre_curso: string;
  estudiantes: EstudianteMatriculado[];
  mensaje: string | null;
}

// =========================== Lecciones y materiales (HU-11) ===========================
export interface LeccionResponse {
  id_curso: string;
  id_leccion: string;
  titulo_leccion: string;
  descripcion_leccion: string | null;
  orden: number;
  duracion_horas: number;
  fecha_creacion: string;
  fecha_edicion: string | null;
}

export interface LeccionCreate {
  id_curso: string;
  titulo_leccion: string;
  descripcion_leccion: string | null;
  orden: number;
  duracion_horas: number;
}

/** La lección no se cambia de curso; por eso aquí no va id_curso. */
export type LeccionUpdate = Partial<Omit<LeccionCreate, 'id_curso'>>;

export type TipoMaterial = 'PDF' | 'VIDEO' | 'DOCUMENTO' | 'ENLACE';

export interface MaterialResponse {
  id_material: string;
  id_leccion: string;
  titulo_material: string;
  tipo_material: TipoMaterial | null;
  URL_archivo: string;
  fecha_creacion: string;
  fecha_edicion: string | null;
}

export interface MaterialCreate {
  id_leccion: string;
  titulo_material: string;
  tipo_material: TipoMaterial;
  URL_archivo: string;
}

export type MaterialUpdate = Partial<MaterialCreate>;

// =========================== Evaluaciones y preguntas (HU-14) ===========================
export interface EvaluacionResponse {
  id_evaluacion: string;
  id_leccion: string;
  nombre_evaluacion: string;
  porcentaje: number;
  nota_minima: number; // escala 0 a 5
  id_usuario_creacion: string;
  id_usuario_edita: string | null;
  fecha_creacion: string;
  fecha_edicion: string | null;
}

export interface EvaluacionCreate {
  id_leccion: string;
  nombre_evaluacion: string;
  porcentaje: number;
  nota_minima: number;
}

/** La evaluación no se cambia de lección; por eso aquí no va id_leccion. */
export type EvaluacionUpdate = Partial<Omit<EvaluacionCreate, 'id_leccion'>>;

export type TipoPregunta = 'OPCION_MULTIPLE' | 'VERDADERO_FALSO';

export interface PreguntaEstudiante {
  id_pregunta: string;
  tipo: TipoPregunta;
  enunciado: string;
  opciones: string[];
  orden: number;
}

export interface PreguntaDocente extends PreguntaEstudiante {
  id_evaluacion: string;
  respuesta_correcta: string;
}

export interface PreguntaCreate {
  tipo: TipoPregunta;
  enunciado: string;
  opciones: string[];
  respuesta_correcta: string;
}

// =========================== Solo lectura para Admin / Docente ===========================
/** RF-03: las notas las pone el sistema al presentar la evaluación (HU-15). */
export interface CalificacionResponse {
  id_inscripcion: string;
  id_evaluacion: string;
  nombre_evaluacion: string | null;
  nombre_estudiante: string | null;
  nombre_curso: string | null;
  Nota: number;
  fecha_creacion: string;
  fecha_edicion: string | null;
}

/** RF-11: los pagos los registra el sistema en el checkout (HU-09). */
export interface PagoResponse {
  id_pago: string;
  id_usuario: string;
  nombre_estudiante: string | null;
  id_curso: string;
  nombre_curso: string | null;
  monto: number;
  estado_pago: 'APROBADO' | 'RECHAZADO';
  metodo_pago: string;
  referencia: string | null;
  fecha_creacion: string;
  fecha_edicion: string | null;
}

export interface FiltroPagos {
  id_curso?: string;
  id_estudiante?: string;
  desde?: string; // AAAA-MM-DD
  hasta?: string;
}

/** HU-13: los certificados los emite el sistema al aprobar el curso (HU-16). */
export interface CertificadoResponse {
  id_certificado: string;
  id_inscripcion: string;
  codigo_verificacion: string | null;
  promedio_final: number | null;
  nombre_estudiante: string | null;
  nombre_curso: string | null;
  fecha_creacion: string;
  fecha_edicion: string | null;
}

export type EstadoInscripcion = 'PENDIENTE' | 'ACTIVA' | 'CANCELADA' | 'APROBADA' | 'REPROBADA' | 'FINALIZADA';

/** RF-10 / HU-17: inscripciones vistas por el Admin. */
export interface InscripcionResponse {
  id_inscripcion: string;
  id_curso: string;
  nombre_curso: string | null;
  id_usuario_inscrito: string;
  nombre_estudiante: string | null;
  estado_inscripcion: EstadoInscripcion;
  promedio_final: number | null;
  codigo_certificado: string | null;
  fecha_creacion: string;
  fecha_edicion: string | null;
}

/** RF-10: matrícula manual del Admin (queda ACTIVA). */
export interface InscripcionCreate {
  id_curso: string;
  id_usuario_inscrito: string;
}

// =========================== Recorrido del estudiante ===========================
/** HU-09: datos del pago (tarjeta o PSE). */
export interface CheckoutRequest {
  metodo_pago: 'TARJETA' | 'PSE';
  numero_tarjeta?: string;
  titular?: string;
  banco?: string;
  tipo_persona?: 'NATURAL' | 'JURIDICA';
}

export interface CheckoutResponse {
  aprobado: boolean;
  mensaje: string;
  referencia: string;
  id_pago: string;
  monto: number;
  metodo_pago: string;
  id_inscripcion: string;
  estado_inscripcion: EstadoInscripcion;
}

/** HU-12: un curso en "Mis cursos". */
export interface MiCurso {
  id_inscripcion: string;
  id_curso: string;
  nombre_curso: string;
  descripcion_curso: string | null;
  duracion_horas: number;
  estado_inscripcion: EstadoInscripcion;
  porcentaje_avance: number;
}

export interface MaterialAula {
  id_material: string;
  titulo_material: string;
  tipo_material: TipoMaterial | null;
  URL_archivo: string;
}

export interface EvaluacionAula {
  id_evaluacion: string;
  nombre_evaluacion: string;
  porcentaje: number;
  nota_minima: number;
  nota_obtenida: number | null;
  aprobada: boolean; // HU-15 esc. 3: si ya la aprobó, se ve en solo lectura
}

export interface LeccionAula {
  id_leccion: string;
  orden: number;
  titulo_leccion: string;
  descripcion_leccion: string | null;
  duracion_horas: number;
  completada: boolean;
  materiales: MaterialAula[];
  evaluacion: EvaluacionAula | null;
}

export interface ContenidoCurso {
  id_inscripcion: string;
  id_curso: string;
  nombre_curso: string;
  estado_inscripcion: EstadoInscripcion;
  porcentaje_avance: number;
  evaluaciones_pendientes: number;
  lecciones_pendientes: number;
  mensaje_cierre: string | null; // HU-16 esc. 3
  certificado_disponible: boolean; // HU-13
  mensaje_certificado: string | null; // HU-13 esc. 2 y 3
  lecciones: LeccionAula[];
}

export interface ResultadoEvaluacion {
  id_inscripcion: string;
  id_evaluacion: string;
  correctas: number;
  total: number;
  nota: number;
  nota_minima: number;
  aprobada: boolean;
  numero_intento: number; // RF-13
  estado_curso: EstadoInscripcion | null; // HU-16: si con esta se cerró el curso
  promedio_curso: number | null;
  mensaje: string;
}

/** HU-15 esc. 3: resultado anterior en solo lectura, con todos los intentos (RF-13). */
export interface IntentoEvaluacion {
  numero_intento: number;
  nota: number;
  correctas: number;
  total: number;
  fecha: string;
}

export interface MiResultado {
  id_evaluacion: string;
  nombre_evaluacion: string;
  nota: number | null;
  nota_minima: number;
  aprobada: boolean;
  puede_presentar: boolean;
  intentos: IntentoEvaluacion[];
}

/** RF-07: historial de cambios de contenidos activos (usuario, fecha y detalle). Solo lo consulta el Admin. */
export type EntidadHistorial = 'CURSO' | 'LECCION' | 'MATERIAL' | 'EVALUACION' | 'PREGUNTA' | 'CATEGORIA';

export interface HistorialCambioResponse {
  id_historial: string;
  entidad: EntidadHistorial;
  id_registro: string;
  nombre_registro: string | null;
  accion: 'ACTUALIZAR' | 'ELIMINAR';
  detalle: string;
  id_usuario: string;
  nombre_usuario: string | null;
  rol_usuario: Rol | null;
  fecha: string;
}

export interface FiltroHistorial {
  entidad?: string;
  id_usuario?: string;
  desde?: string; // AAAA-MM-DD
  hasta?: string;
}
