import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { MaterialCreate, MaterialResponse, MaterialUpdate } from '../../models/api.models';

/** HU-11 esc. 2: materiales de una lección (PDF, video, documento o enlace). */
@Injectable({ providedIn: 'root' })
export class MaterialService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/material`;

  list(idLeccion?: string): Observable<MaterialResponse[]> {
    return this.http.get<MaterialResponse[]>(this.base, { params: idLeccion ? { id_leccion: idLeccion } : {} });
  }

  create(body: MaterialCreate): Observable<MaterialResponse> {
    return this.http.post<MaterialResponse>(this.base, body);
  }

  update(id: string, body: MaterialUpdate): Observable<MaterialResponse> {
    return this.http.put<MaterialResponse>(`${this.base}/${id}`, body);
  }

  delete(id: string): Observable<void> {
    return this.http.delete(`${this.base}/${id}`).pipe(map(() => undefined));
  }
}
