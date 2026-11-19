import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { CategoriaCreate, CategoriaResponse } from '../../models/api.models';

/** HU-04 esc. 1: crear lo puede el Admin o el Docente; editar y eliminar solo el Admin. */
@Injectable({ providedIn: 'root' })
export class CategoriaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/categorias`;

  list(): Observable<CategoriaResponse[]> {
    return this.http.get<CategoriaResponse[]>(this.base, { params: { limit: 500 } });
  }

  create(body: CategoriaCreate): Observable<CategoriaResponse> {
    return this.http.post<CategoriaResponse>(this.base, body);
  }

  update(id: string, body: CategoriaCreate): Observable<CategoriaResponse> {
    return this.http.put<CategoriaResponse>(`${this.base}/${id}`, body);
  }

  delete(id: string): Observable<void> {
    return this.http.delete(`${this.base}/${id}`).pipe(map(() => undefined));
  }
}
