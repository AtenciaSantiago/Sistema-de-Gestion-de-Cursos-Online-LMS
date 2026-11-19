import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { InscripcionCreate, InscripcionResponse } from '../../models/api.models';

/**
 * RF-10 y HU-17 (solo Admin). El estado de la inscripción lo cambia el SISTEMA (pago y cierre);
 * al Admin solo le quedan la matrícula manual y la cancelación. Nunca aprueba a nadie.
 */
@Injectable({ providedIn: 'root' })
export class InscripcionService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/inscripciones`;

  list(estado?: string): Observable<InscripcionResponse[]> {
    const params: Record<string, string | number> = { limit: 500 };
    if (estado) params['estado'] = estado;
    return this.http.get<InscripcionResponse[]>(this.base, { params });
  }

  /** HU-17: solo las inscripciones cerradas (APROBADA, REPROBADA o FINALIZADA). */
  cierres(estado?: string): Observable<InscripcionResponse[]> {
    return this.http.get<InscripcionResponse[]>(`${this.base}/cierres`, { params: estado ? { estado } : {} });
  }

  matricular(body: InscripcionCreate): Observable<InscripcionResponse> {
    return this.http.post<InscripcionResponse>(this.base, body);
  }

  cancelar(id: string): Observable<InscripcionResponse> {
    return this.http.put<InscripcionResponse>(`${this.base}/${id}/cancelar`, {});
  }
}
