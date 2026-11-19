import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { CalificacionResponse } from '../../models/api.models';

/**
 * RF-03: solo lectura. Las notas las pone el sistema cuando el estudiante presenta (HU-15);
 * por eso aquí ya no hay crear, editar ni borrar.
 */
@Injectable({ providedIn: 'root' })
export class CalificacionService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/calificaciones`;

  list(): Observable<CalificacionResponse[]> {
    return this.http.get<CalificacionResponse[]>(this.base, { params: { limit: 500 } });
  }
}
