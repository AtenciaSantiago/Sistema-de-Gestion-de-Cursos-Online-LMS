import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { EvaluacionCreate, EvaluacionResponse, EvaluacionUpdate } from '../../models/api.models';

/** HU-14: evaluaciones de las lecciones (una por lección). Las preguntas van en PreguntaService. */
@Injectable({ providedIn: 'root' })
export class EvaluacionService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/evaluaciones`;

  list(): Observable<EvaluacionResponse[]> {
    return this.http.get<EvaluacionResponse[]>(this.base);
  }

  create(body: EvaluacionCreate): Observable<EvaluacionResponse> {
    return this.http.post<EvaluacionResponse>(this.base, body);
  }

  update(id: string, body: EvaluacionUpdate): Observable<EvaluacionResponse> {
    return this.http.put<EvaluacionResponse>(`${this.base}/${id}`, body);
  }

  delete(id: string): Observable<void> {
    return this.http.delete(`${this.base}/${id}`).pipe(map(() => undefined));
  }

  /** HU-14 esc. 2: si algún estudiante ya la presentó, ya no se puede modificar. */
  editable(id: string): Observable<{ editable: boolean; mensaje: string | null }> {
    return this.http.get<{ editable: boolean; mensaje: string | null }>(`${this.base}/${id}/editable`);
  }
}
