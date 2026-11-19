import { Rol } from '../models/api.models';

/**
 * Datos de la sesión que guarda el login (HU-01).
 * Ojo: esto solo decide qué se MUESTRA. Quien de verdad protege los datos es el backend,
 * que revisa el rol en cada petición (RN-02).
 */
export function rolActual(): Rol | null {
  return (localStorage.getItem('rol') as Rol | null) ?? null;
}

export function idUsuarioActual(): string | null {
  return localStorage.getItem('id_usuario');
}

export function esAdmin(): boolean {
  return rolActual() === 'Admin';
}

export function guardarSesion(datos: { access_token: string; id_usuario: string; nombre_usuario: string; rol: Rol }): void {
  localStorage.setItem('token', datos.access_token);
  localStorage.setItem('id_usuario', datos.id_usuario);
  localStorage.setItem('nombre_usuario', datos.nombre_usuario);
  localStorage.setItem('rol', datos.rol);
}

export function cerrarSesion(): void {
  for (const clave of ['token', 'id_usuario', 'nombre_usuario', 'rol', 'pos_audit_usuario_id']) {
    localStorage.removeItem(clave);
  }
}
