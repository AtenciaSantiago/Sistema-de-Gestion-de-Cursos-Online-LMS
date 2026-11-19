import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { CertificadoResponse } from '../../models/api.models';

/**
 * HU-13 / RF-16: los certificados los emite el sistema al aprobar el curso (HU-16).
 * Un certificado emitido es inalterable: no se edita ni se borra.
 */
@Injectable({ providedIn: 'root' })
export class CertificadoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/certificados`;

  /** Solo consulta: el Admin ve los certificados emitidos por el cierre automático. */
  list(): Observable<CertificadoResponse[]> {
    return this.http.get<CertificadoResponse[]>(this.base, { params: { limit: 500 } });
  }
}
