import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { CursoCreate, CursoResponse, CursoUpdate, ReporteEstudiantes } from '../../models/api.models';

/** HU-04, HU-05, HU-07 y HU-10. El Admin ve todos los cursos; el Docente solo los asignados. */
@Injectable({ providedIn: 'root' })
export class CursoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/cursos`;

  list(): Observable<CursoResponse[]> {
    return this.http.get<CursoResponse[]>(this.base, { params: { limit: 500 } });
  }

  create(body: CursoCreate): Observable<CursoResponse> {
    return this.http.post<CursoResponse>(this.base, body);
  }

  update(id: string, body: CursoUpdate): Observable<CursoResponse> {
    return this.http.put<CursoResponse>(`${this.base}/${id}`, body);
  }

  delete(id: string): Observable<void> {
    return this.http.delete(`${this.base}/${id}`).pipe(map(() => undefined));
  }

  /** HU-10: estudiantes con inscripción ACTIVA en el curso. */
  estudiantes(id: string): Observable<ReporteEstudiantes> {
    return this.http.get<ReporteEstudiantes>(`${this.base}/${id}/estudiantes`);
  }
}
