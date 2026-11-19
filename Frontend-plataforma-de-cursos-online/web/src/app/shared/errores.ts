import { HttpErrorResponse } from '@angular/common/http';
import { AbstractControl, FormGroup } from '@angular/forms';

/**
 * Entregable 2: un solo lugar para convertir un error de la API en un mensaje para el usuario.
 * (Antes cada pantalla tenía su propia copia de esta función.)
 * El backend siempre responde { detail: "mensaje" } y, si faltan datos, también { campos: [...] }.
 */
export function mensajeError(err: HttpErrorResponse): string {
  if (err.status === 0) {
    return 'No se pudo conectar con el servidor. Revise que la API esté encendida';
  }
  const detalle = err.error?.detail;
  if (typeof detalle === 'string') {
    return detalle;
  }
  if (Array.isArray(detalle)) {
    return detalle.map((x) => x.msg ?? JSON.stringify(x)).join('; ');
  }
  return err.message;
}

/**
 * HU-02 esc. 3 y HU-04 esc. 4: si la API dice qué campos faltan, se marcan en rojo en el formulario.
 */
export function marcarCamposConError(err: HttpErrorResponse, form: FormGroup): void {
  const campos: string[] = err.error?.campos ?? [];
  for (const nombre of campos) {
    const control: AbstractControl | null = form.get(nombre);
    if (control) {
      control.setErrors({ ...(control.errors ?? {}), servidor: true });
      control.markAsTouched();
    }
  }
}

/**
 * Entregable 3 (HU-02 esc. 2 y HU-03 esc. 4): cuando la API rechaza un dato repetido responde 400 con un
 * mensaje y sin la lista «campos». Aquí se busca en el mensaje de qué dato habla y se resalta ese campo.
 */
export function marcarCampoRepetido(err: HttpErrorResponse, form: FormGroup): void {
  const detalle = typeof err.error?.detail === 'string' ? err.error.detail.toLowerCase() : '';
  const campo = detalle.includes('correo')
    ? 'email'
    : detalle.includes('documento')
      ? 'documento_identidad'
      : detalle.includes('nombre de usuario')
        ? 'nombre_usuario'
        : null;
  const control = campo ? form.get(campo) : null;
  if (err.status === 400 && control) {
    control.setErrors({ ...(control.errors ?? {}), repetido: true });
    control.markAsTouched();
  }
}

/** Mensaje del E1 cuando el usuario deja campos obligatorios vacíos (lo usa también el formulario). */
export const MENSAJE_CAMPOS_OBLIGATORIOS = 'Por favor complete todos los campos obligatorios';
