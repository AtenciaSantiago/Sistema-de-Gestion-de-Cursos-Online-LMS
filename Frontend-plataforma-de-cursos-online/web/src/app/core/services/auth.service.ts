import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { LoginResponse } from '../../models/api.models';
import { cerrarSesion } from '../sesion';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly api = environment.apiUrl;

  /** HU-01: se puede escribir el correo o el nombre de usuario. */
  login(datos: { nombre_usuario: string; contrasena: string }): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.api}/usuarios/login`, datos);
  }

  logout(): void {
    cerrarSesion();
  }
}
