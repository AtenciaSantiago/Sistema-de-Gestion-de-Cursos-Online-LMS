import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { LeccionService } from '../../core/services/leccion.service';
import { LeccionResponse } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';

export interface LeccionDialogData {
  mode: 'create' | 'edit';
  idCurso: string;
  row?: LeccionResponse;
  ordenSugerido?: number;
}

/** HU-11 esc. 4: mensaje exacto del E1 si falta el título o el número de orden. */
const MENSAJE_TITULO_Y_ORDEN = 'Debe asignar un título y un número de orden a la lección';

/** HU-11 esc. 1: título, descripción y número de orden. La lección no se cambia de curso. */
@Component({
  selector: 'app-leccion-dialog',
  imports: [ReactiveFormsModule, MatDialogModule, MatButtonModule, MatFormFieldModule, MatInputModule, MatSnackBarModule],
  templateUrl: './leccion-dialog.html',
})
export class LeccionDialogComponent {
  private readonly fb = inject(FormBuilder);
  private readonly leccionService = inject(LeccionService);
  private readonly dialogRef = inject(MatDialogRef<LeccionDialogComponent, boolean>);
  private readonly snack = inject(MatSnackBar);
  readonly data = inject<LeccionDialogData>(MAT_DIALOG_DATA);
  readonly guardando = signal(false);

  readonly form = this.fb.nonNullable.group({
    titulo_leccion: [this.data.row?.titulo_leccion ?? '', [Validators.required, Validators.maxLength(150)]],
    descripcion_leccion: [this.data.row?.descripcion_leccion ?? ''],
    orden: [this.data.row?.orden ?? this.data.ordenSugerido ?? 1, [Validators.required, Validators.min(1)]],
    duracion_horas: [this.data.row?.duracion_horas ?? 1, [Validators.required, Validators.min(1)]],
  });

  cancel(): void {
    this.dialogRef.close(false);
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.snack.open(MENSAJE_TITULO_Y_ORDEN, 'Cerrar', { duration: 4000 });
      return;
    }
    const v = this.form.getRawValue();
    const datos = { ...v, descripcion_leccion: v.descripcion_leccion || null };
    const peticion =
      this.data.mode === 'create'
        ? this.leccionService.create({ ...datos, id_curso: this.data.idCurso })
        : this.leccionService.update(this.data.row!.id_leccion, datos);

    this.guardando.set(true);
    peticion.subscribe({
      next: () => this.dialogRef.close(true),
      error: (err: HttpErrorResponse) => {
        this.guardando.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }); // ej. orden repetido
      },
    });
  }
}
