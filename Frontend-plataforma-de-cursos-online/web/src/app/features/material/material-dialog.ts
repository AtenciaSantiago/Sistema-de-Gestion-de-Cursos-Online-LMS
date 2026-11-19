import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { MaterialService } from '../../core/services/material.service';
import { MaterialResponse, TipoMaterial } from '../../models/api.models';
import { MENSAJE_CAMPOS_OBLIGATORIOS, mensajeError } from '../../shared/errores';

export interface MaterialDialogData {
  mode: 'create' | 'edit';
  idLeccion: string;
  row?: MaterialResponse;
}

/** HU-11 esc. 2: nombre, tipo y enlace del material. */
@Component({
  selector: 'app-material-dialog',
  imports: [ReactiveFormsModule, MatDialogModule, MatButtonModule, MatFormFieldModule, MatInputModule, MatSelectModule, MatSnackBarModule],
  templateUrl: './material-dialog.html',
})
export class MaterialDialogComponent {
  private readonly fb = inject(FormBuilder);
  private readonly materialService = inject(MaterialService);
  private readonly dialogRef = inject(MatDialogRef<MaterialDialogComponent, boolean>);
  private readonly snack = inject(MatSnackBar);
  readonly data = inject<MaterialDialogData>(MAT_DIALOG_DATA);
  readonly guardando = signal(false);

  readonly tipos: { valor: TipoMaterial; texto: string }[] = [
    { valor: 'PDF', texto: 'Archivo PDF' },
    { valor: 'VIDEO', texto: 'Video' },
    { valor: 'DOCUMENTO', texto: 'Documento' },
    { valor: 'ENLACE', texto: 'Enlace web' },
  ];

  readonly form = this.fb.nonNullable.group({
    titulo_material: [this.data.row?.titulo_material ?? '', [Validators.required, Validators.maxLength(150)]],
    tipo_material: [(this.data.row?.tipo_material ?? 'PDF') as TipoMaterial, Validators.required],
    // Igual que la API: dirección web completa
    URL_archivo: [this.data.row?.URL_archivo ?? '', [Validators.required, Validators.pattern(/^https?:\/\/\S+\.\S+/i)]],
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
    const datos = { ...this.form.getRawValue(), id_leccion: this.data.idLeccion };
    const peticion =
      this.data.mode === 'create'
        ? this.materialService.create(datos)
        : this.materialService.update(this.data.row!.id_material, datos);

    this.guardando.set(true);
    peticion.subscribe({
      next: () => this.dialogRef.close(true),
      error: (err: HttpErrorResponse) => {
        this.guardando.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 });
      },
    });
  }
}
