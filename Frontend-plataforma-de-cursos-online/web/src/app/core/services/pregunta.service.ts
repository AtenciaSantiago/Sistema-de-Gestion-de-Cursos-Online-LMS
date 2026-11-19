import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { PreguntaCreate, PreguntaDocente } from '../../models/api.models';

/** HU-14: el docente arma las preguntas de una evaluación (el backend las crea con la Factory). */
@Injectable({ providedIn: 'root' })
export class PreguntaService {
  private readonly http = inject(HttpClient);
  private readonly api = environment.apiUrl;

  /** El docente las ve CON la respuesta correcta. */
  listarConClave(idEvaluacion: string): Observable<PreguntaDocente[]> {
    return this.http.get<PreguntaDocente[]>(`${this.api}/evaluaciones/${idEvaluacion}/preguntas/clave`);
  }

  crear(idEvaluacion: string, body: PreguntaCreate): Observable<PreguntaDocente> {
    return this.http.post<PreguntaDocente>(`${this.api}/evaluaciones/${idEvaluacion}/preguntas`, body);
  }

  actualizar(idPregunta: string, body: Partial<PreguntaCreate>): Observable<PreguntaDocente> {
    return this.http.put<PreguntaDocente>(`${this.api}/preguntas/${idPregunta}`, body);
  }

  eliminar(idPregunta: string): Observable<void> {
    return this.http.delete(`${this.api}/preguntas/${idPregunta}`).pipe(map(() => undefined));
  }
}
