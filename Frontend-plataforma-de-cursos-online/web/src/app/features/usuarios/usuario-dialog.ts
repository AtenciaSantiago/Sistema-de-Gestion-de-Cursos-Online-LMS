import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { idUsuarioActual } from '../../core/sesion';
import { UsuarioService } from '../../core/services/usuario.service';
import { Rol, UsuarioResponse, UsuarioUpdate } from '../../models/api.models';
import { MENSAJE_CAMPOS_OBLIGATORIOS, marcarCampoRepetido, marcarCamposConError, mensajeError } from '../../shared/errores';

export interface UsuarioDialogData {
  mode: 'create' | 'edit';
  row?: UsuarioResponse;
}

/** HU-03 esc. 1 y 2: crear cuentas (incluidos docentes y admins) y cambiar datos o rol. */
@Component({
  selector: 'app-usuario-dialog',
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatCheckboxModule,
    MatSnackBarModule,
  ],
  templateUrl: './usuario-dialog.html',
})
export class UsuarioDialogComponent {
  private readonly fb = inject(FormBuilder);
  private readonly usuarioService = inject(UsuarioService);
  private readonly dialogRef = inject(MatDialogRef<UsuarioDialogComponent, boolean>);
  private readonly snack = inject(MatSnackBar);
  readonly data = inject<UsuarioDialogData>(MAT_DIALOG_DATA);

  /** Al editarse a sí mismo no puede quitarse el rol de Admin ni desactivarse. */
  readonly esMiCuenta = this.data.row?.id_usuario === idUsuarioActual();
  readonly guardando = signal(false);

  readonly form = this.fb.nonNullable.group({
    nombre_usuario: ['', [Validators.required, Validators.pattern(/^[^@]+$/)]],
    tipo_documento: ['CC', Validators.required],
    documento_identidad: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    // Obligatoria al crear; al editar, vacía = no se cambia. Mínimo 8, igual que la API.
    contrasena: ['', this.data.mode === 'create' ? [Validators.required, Validators.minLength(8)] : [Validators.minLength(8)]],
    rol: ['Estudiante' as Rol, Validators.required],
    activo: [true],
  });

  constructor() {
    const r = this.data.row;
    if (this.data.mode === 'edit' && r) {
      this.form.patchValue({ ...r, contrasena: '' });
    }
    if (this.esMiCuenta) {
      this.form.controls.rol.disable();
      this.form.controls.activo.disable();
    }
  }

  cancel(): void {
    this.dialogRef.close(false);
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.snack.open(MENSAJE_CAMPOS_OBLIGATORIOS, 'Cerrar', { duration: 4000 });
      return;
    }
    const { contrasena, ...resto } = this.form.getRawValue();
    const peticion =
      this.data.mode === 'create'
        ? this.usuarioService.create({ ...resto, contrasena })
        : this.usuarioService.update(this.data.row!.id_usuario, {
            ...(this.esMiCuenta ? { ...resto, rol: undefined, activo: undefined } : resto),
            ...(contrasena ? { contrasena } : {}),
          } as UsuarioUpdate);

    this.guardando.set(true);
    peticion.subscribe({
      next: () => this.dialogRef.close(true),
      error: (err: HttpErrorResponse) => {
        this.guardando.set(false);
        marcarCamposConError(err, this.form);
        marcarCampoRepetido(err, this.form); // Entregable 3: correo, documento o usuario repetido
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 });
      },
    });
  }
}
