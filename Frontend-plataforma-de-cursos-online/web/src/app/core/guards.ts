import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { Rol } from '../models/api.models';
import { rolActual } from './sesion';

/** Sin sesión iniciada no se entra a la aplicación (HU-01). */
export const sesionGuard: CanActivateFn = () => {
  const router = inject(Router);
  return localStorage.getItem('token') ? true : router.createUrlTree(['/login']);
};

/**
 * RN-02: cada pantalla solo la abre el rol que le corresponde. Si un estudiante escribe
 * a mano /app/usuarios, se le devuelve a su inicio (el backend igual respondería 403).
 */
export function rolGuard(...roles: Rol[]): CanActivateFn {
  return () => {
    const router = inject(Router);
    const rol = rolActual();
    return rol && roles.includes(rol) ? true : router.createUrlTree(['/app']);
  };
}

/** Página de inicio según el rol. */
export function inicioSegunRol(): string {
  return rolActual() === 'Estudiante' ? 'catalogo' : 'cursos';
}
