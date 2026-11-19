import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { UsuarioCreate, UsuarioResponse, UsuarioUpdate } from '../../models/api.models';

/** HU-02 (registro) y HU-03 (administración de cuentas, solo Admin). */
@Injectable({ providedIn: 'root' })
export class UsuarioService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/usuarios`;

  list(): Observable<UsuarioResponse[]> {
    return this.http.get<UsuarioResponse[]>(this.base, { params: { limit: 500 } });
  }

  create(body: UsuarioCreate): Observable<UsuarioResponse> {
    return this.http.post<UsuarioResponse>(this.base, body);
  }

  update(id: string, body: UsuarioUpdate): Observable<UsuarioResponse> {
    return this.http.put<UsuarioResponse>(`${this.base}/${id}`, body);
  }

  delete(id: string): Observable<void> {
    return this.http.delete(`${this.base}/${id}`).pipe(map(() => undefined));
  }

  /** El login solo necesita saber si existe algún usuario (la lista completa no es pública). */
  hayUsuarios(): Observable<{ hay_usuarios: boolean }> {
    return this.http.get<{ hay_usuarios: boolean }>(`${this.base}/hay-usuarios`);
  }
}
