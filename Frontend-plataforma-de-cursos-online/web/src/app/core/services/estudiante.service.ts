import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  CheckoutRequest,
  CheckoutResponse,
  ContenidoCurso,
  CursoResponse,
  MiCurso,
  MiResultado,
  PreguntaEstudiante,
  ResultadoEvaluacion,
} from '../../models/api.models';

/**
 * Entregable 2: todo lo que usa el estudiante en su recorrido.
 * Catálogo (HU-06) -> Pago (HU-09) -> Aula y progreso (HU-12) -> Evaluación (HU-15) -> Certificado (HU-13)
 */
@Injectable({ providedIn: 'root' })
export class EstudianteService {
  private readonly http = inject(HttpClient);
  private readonly api = environment.apiUrl;

  /** HU-06: cursos PUBLICADOS; con filtro opcional por categoría. */
  catalogo(idCategoria?: string): Observable<CursoResponse[]> {
    return this.http.get<CursoResponse[]>(`${this.api}/catalogo`, { params: idCategoria ? { id_categoria: idCategoria } : {} });
  }

  pagarCurso(idCurso: string, body: CheckoutRequest): Observable<CheckoutResponse> {
    return this.http.post<CheckoutResponse>(`${this.api}/checkout/cursos/${idCurso}`, body);
  }

  misCursos(): Observable<MiCurso[]> {
    return this.http.get<MiCurso[]>(`${this.api}/mis-cursos`);
  }

  contenido(idCurso: string): Observable<ContenidoCurso> {
    return this.http.get<ContenidoCurso>(`${this.api}/mis-cursos/${idCurso}`);
  }

  /** HU-12. Si con esta lección quedó todo completo, el curso se cierra (HU-16) y llega estado_curso. */
  marcarCompletada(idLeccion: string): Observable<{ porcentaje_avance: number; mensaje: string; estado_curso: string | null }> {
    return this.http.post<{ porcentaje_avance: number; mensaje: string; estado_curso: string | null }>(
      `${this.api}/mis-cursos/lecciones/${idLeccion}/completar`,
      {},
    );
  }

  preguntas(idEvaluacion: string): Observable<PreguntaEstudiante[]> {
    return this.http.get<PreguntaEstudiante[]>(`${this.api}/evaluaciones/${idEvaluacion}/preguntas`);
  }

  presentar(idEvaluacion: string, respuestas: Record<string, string>): Observable<ResultadoEvaluacion> {
    return this.http.post<ResultadoEvaluacion>(`${this.api}/evaluaciones/${idEvaluacion}/presentar`, { respuestas });
  }

  /** HU-15 esc. 3: resultado anterior en solo lectura con todos sus intentos (RF-13). */
  miResultado(idEvaluacion: string): Observable<MiResultado> {
    return this.http.get<MiResultado>(`${this.api}/evaluaciones/${idEvaluacion}/mi-resultado`);
  }

  /** HU-13: el PDF del certificado (solo si el curso quedó APROBADO). */
  certificado(idCurso: string): Observable<Blob> {
    return this.http.get(`${this.api}/mis-cursos/${idCurso}/certificado`, { responseType: 'blob' });
  }
}
