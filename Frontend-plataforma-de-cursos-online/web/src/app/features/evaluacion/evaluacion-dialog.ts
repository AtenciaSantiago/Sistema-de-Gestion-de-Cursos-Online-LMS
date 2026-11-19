import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { EvaluacionService } from '../../core/services/evaluacion.service';
import { EvaluacionResponse, LeccionResponse } from '../../models/api.models';
import { MENSAJE_CAMPOS_OBLIGATORIOS, mensajeError } from '../../shared/errores';

export interface EvaluacionDialogData {
  mode: 'create' | 'edit';
  leccion: LeccionResponse;
  row?: EvaluacionResponse;
  disponible: number; // porcentaje que todavía queda libre en el curso
}

/** HU-14 esc. 3: mensaje del E1 cuando la nota de aprobación no es válida. */
const MENSAJE_NOTA_INVALIDA = 'Debe seleccionar la respuesta correcta y definir una nota de aprobación válida';

/** HU-14: nombre, porcentaje dentro del curso y nota mínima (0 a 5) de la evaluación de una lección. */
@Component({
  selector: 'app-evaluacion-dialog',
  imports: [ReactiveFormsModule, MatDialogModule, MatButtonModule, MatFormFieldModule, MatInputModule, MatSnackBarModule],
  templateUrl: './evaluacion-dialog.html',
})
export class EvaluacionDialogComponent {
  private readonly fb = inject(FormBuilder);
  private readonly evaluacionService = inject(EvaluacionService);
  private readonly dialogRef = inject(MatDialogRef<EvaluacionDialogComponent, boolean>);
  private readonly snack = inject(MatSnackBar);
  readonly data = inject<EvaluacionDialogData>(MAT_DIALOG_DATA);
  readonly guardando = signal(false);

  readonly form = this.fb.nonNullable.group({
    nombre_evaluacion: [this.data.row?.nombre_evaluacion ?? '', [Validators.required, Validators.maxLength(150)]],
    porcentaje: [this.data.row?.porcentaje ?? this.data.disponible, [Validators.required, Validators.min(1), Validators.max(this.data.disponible)]],
    nota_minima: [this.data.row?.nota_minima ?? 3, [Validators.required, Validators.min(0), Validators.max(5)]],
  });

  cancel(): void {
    this.dialogRef.close(false);
  }

  /** Entregable 3: cada dato inválido tiene su propio mensaje (antes el porcentaje solo decía «Revise los campos marcados»). */
  private mensajeFormulario(): string {
    const c = this.form.controls;
    if (c.nombre_evaluacion.invalid) {
      return MENSAJE_CAMPOS_OBLIGATORIOS;
    }
    if (c.porcentaje.invalid) {
      return `El porcentaje debe estar entre 1 y ${this.data.disponible} %: los porcentajes de las evaluaciones del curso no pueden pasar de 100 %`;
    }
    return MENSAJE_NOTA_INVALIDA; // HU-14 esc. 3
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.snack.open(this.mensajeFormulario(), 'Cerrar', { duration: 5000 });
      return;
    }
    const v = this.form.getRawValue();
    const peticion =
      this.data.mode === 'create'
        ? this.evaluacionService.create({ ...v, id_leccion: this.data.leccion.id_leccion })
        : this.evaluacionService.update(this.data.row!.id_evaluacion, v);

    this.guardando.set(true);
    peticion.subscribe({
      next: () => this.dialogRef.close(true),
      error: (err: HttpErrorResponse) => {
        this.guardando.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }); // ej. ya fue presentada
      },
    });
  }
}
