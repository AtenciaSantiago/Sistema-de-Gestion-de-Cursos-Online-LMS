import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { FiltroPagos, PagoResponse } from '../../models/api.models';

/**
 * RF-11: auditoría de pagos, solo lectura. Los pagos los registra el sistema en el checkout (HU-09),
 * aprobados o rechazados; nadie los puede inventar ni editar a mano.
 */
@Injectable({ providedIn: 'root' })
export class PagoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/pago`;

  list(filtro: FiltroPagos = {}): Observable<PagoResponse[]> {
    const params: Record<string, string | number> = { limit: 500 };
    for (const [clave, valor] of Object.entries(filtro)) {
      if (valor) params[clave] = valor;
    }
    return this.http.get<PagoResponse[]>(this.base, { params });
  }
}
