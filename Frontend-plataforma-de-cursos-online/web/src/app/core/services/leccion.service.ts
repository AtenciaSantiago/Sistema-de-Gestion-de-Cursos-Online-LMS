import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { LeccionCreate, LeccionResponse, LeccionUpdate } from '../../models/api.models';

/** HU-11: lecciones de un curso, con su número de orden. */
@Injectable({ providedIn: 'root' })
export class LeccionService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/lecciones`;

  /** Si se manda el curso, solo las lecciones de ese curso (en orden). */
  list(idCurso?: string): Observable<LeccionResponse[]> {
    return this.http.get<LeccionResponse[]>(this.base, { params: idCurso ? { id_curso: idCurso } : {} });
  }

  create(body: LeccionCreate): Observable<LeccionResponse> {
    return this.http.post<LeccionResponse>(this.base, body);
  }

  update(id: string, body: LeccionUpdate): Observable<LeccionResponse> {
    return this.http.put<LeccionResponse>(`${this.base}/${id}`, body);
  }

  delete(id: string): Observable<void> {
    return this.http.delete(`${this.base}/${id}`).pipe(map(() => undefined));
  }
}
