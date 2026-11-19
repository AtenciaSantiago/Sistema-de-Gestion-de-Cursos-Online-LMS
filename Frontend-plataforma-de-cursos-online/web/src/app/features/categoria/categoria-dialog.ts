import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { CategoriaService } from '../../core/services/categoria.service';
import { CategoriaResponse } from '../../models/api.models';
import { MENSAJE_CAMPOS_OBLIGATORIOS, mensajeError } from '../../shared/errores';

export interface CategoriaDialogData {
  mode: 'create' | 'edit';
  row?: CategoriaResponse;
}

/** HU-04 esc. 1. Quién la crea o edita lo toma el backend del token (ya no se manda desde aquí). */
@Component({
  selector: 'app-categoria-dialog',
  imports: [ReactiveFormsModule, MatDialogModule, MatButtonModule, MatFormFieldModule, MatInputModule, MatSnackBarModule],
  templateUrl: './categoria-dialog.html',
})
export class CategoriaDialogComponent {
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(CategoriaService);
  private readonly dialogRef = inject(MatDialogRef<CategoriaDialogComponent, boolean>);
  private readonly snack = inject(MatSnackBar);
  readonly data = inject<CategoriaDialogData>(MAT_DIALOG_DATA);
  readonly guardando = signal(false);

  readonly form = this.fb.nonNullable.group({
    nombre_categoria: [this.data.row?.nombre_categoria ?? '', [Validators.required, Validators.maxLength(150)]],
  });

  cancel(): void {
    this.dialogRef.close(false);
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.snack.open(MENSAJE_CAMPOS_OBLIGATORIOS, 'Cerrar', { duration: 4000 });
      return;
    }
    const datos = this.form.getRawValue();
    const peticion =
      this.data.mode === 'create' ? this.svc.create(datos) : this.svc.update(this.data.row!.id_categoria, datos);

    this.guardando.set(true);
    peticion.subscribe({
      next: () => this.dialogRef.close(true),
      error: (err: HttpErrorResponse) => {
        this.guardando.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }); // ej. "La categoría ya existe"
      },
    });
  }
}
