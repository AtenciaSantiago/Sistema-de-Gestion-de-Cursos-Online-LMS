import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { cerrarSesion } from '../sesion';

/**
 * Le pone el token a cada petición. Entregable 2: si la API responde 401 (el token venció
 * o el administrador desactivó la cuenta, HU-03 esc. 3) se cierra la sesión y vuelve al login.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const token = localStorage.getItem('token');
  const conToken = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(conToken).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401 && token) {
        cerrarSesion();
        void router.navigate(['/login'], { queryParams: { motivo: 'sesion' } });
      }
      return throwError(() => err);
    }),
  );
};
