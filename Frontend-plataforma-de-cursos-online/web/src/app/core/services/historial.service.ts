import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { FiltroHistorial, HistorialCambioResponse } from '../../models/api.models';

/**
 * RF-07: historial de cambios de contenidos, solo lectura. Los registros los escribe el backend
 * cada vez que alguien edita o elimina un curso, lección, material, evaluación, pregunta o categoría.
 */
@Injectable({ providedIn: 'root' })
export class HistorialService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/historial`;

  list(filtro: FiltroHistorial = {}): Observable<HistorialCambioResponse[]> {
    const params: Record<string, string | number> = { limit: 500 };
    for (const [clave, valor] of Object.entries(filtro)) {
      if (valor) params[clave] = valor;
    }
    return this.http.get<HistorialCambioResponse[]>(this.base, { params });
  }
}
