import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { esAdmin } from '../../core/sesion';
import { CategoriaService } from '../../core/services/categoria.service';
import { CursoService } from '../../core/services/curso.service';
import { UsuarioService } from '../../core/services/usuario.service';
import { CategoriaResponse, CursoCreate, CursoResponse, UsuarioResponse } from '../../models/api.models';
import { MENSAJE_CAMPOS_OBLIGATORIOS, marcarCamposConError, mensajeError } from '../../shared/errores';

export interface CursoDialogData {
  mode: 'create' | 'edit';
  row?: CursoResponse;
}

/**
 * HU-04: crear o editar la información base de un curso.
 * - Obligatorios (esc. 2): nombre, descripción, duración, categoría y profesor asignado.
 * - Todo curso nuevo nace en BORRADOR; publicarlo es otra acción y solo la hace el Admin (HU-05).
 * - El Admin escoge el profesor; si lo crea un Docente, el profesor es él mismo.
 */
@Component({
  selector: 'app-curso-dialog',
  imports: [ReactiveFormsModule, MatDialogModule, MatButtonModule, MatFormFieldModule, MatInputModule, MatSelectModule, MatSnackBarModule],
  templateUrl: './curso-dialog.html',
})
export class CursoDialogComponent {
  private readonly fb = inject(FormBuilder);
  private readonly cursoService = inject(CursoService);
  private readonly categoriaService = inject(CategoriaService);
  private readonly usuarioService = inject(UsuarioService);
  private readonly dialogRef = inject(MatDialogRef<CursoDialogComponent, boolean>);
  private readonly snack = inject(MatSnackBar);
  readonly data = inject<CursoDialogData>(MAT_DIALOG_DATA);

  readonly esAdmin = esAdmin();
  readonly categorias = signal<CategoriaResponse[]>([]);
  readonly docentes = signal<UsuarioResponse[]>([]);
  readonly guardando = signal(false);

  readonly form = this.fb.nonNullable.group({
    id_categoria: ['', Validators.required],
    nombre_curso: ['', [Validators.required, Validators.maxLength(100)]],
    descripcion_curso: ['', Validators.required],
    duracion_horas: [1, [Validators.required, Validators.min(1)]],
    precio: [0, [Validators.required, Validators.min(0)]], // HU-09
    // Solo el Admin lo escoge (para el Docente se ignora: es él mismo)
    id_docente: ['', this.esAdmin ? Validators.required : []],
  });

  constructor() {
    this.categoriaService.list().subscribe({ next: (c) => this.categorias.set(c) });
    if (this.esAdmin) {
      // Solo docentes activos (el backend valida lo mismo)
      this.usuarioService.list().subscribe({
        next: (u) => this.docentes.set(u.filter((x) => x.rol === 'Docente' && x.activo)),
      });
    }

    const r = this.data.row;
    if (this.data.mode === 'edit' && r) {
      this.form.patchValue({
        id_categoria: r.id_categoria,
        nombre_curso: r.nombre_curso,
        descripcion_curso: r.descripcion_curso ?? '',
        duracion_horas: r.duracion_horas,
        precio: r.precio ?? 0,
        id_docente: r.id_docente ?? '',
      });
    }
  }

  cancel(): void {
    this.dialogRef.close(false);
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.snack.open(MENSAJE_CAMPOS_OBLIGATORIOS, 'Cerrar', { duration: 4000 }); // HU-04 esc. 4
      return;
    }
    const v = this.form.getRawValue();
    const datos: CursoCreate = {
      id_categoria: v.id_categoria,
      nombre_curso: v.nombre_curso,
      descripcion_curso: v.descripcion_curso,
      duracion_horas: v.duracion_horas,
      precio: v.precio,
      ...(this.esAdmin ? { id_docente: v.id_docente } : {}),
    };

    const peticion =
      this.data.mode === 'create'
        ? this.cursoService.create(datos)
        : this.cursoService.update(this.data.row!.id_curso, datos);

    this.guardando.set(true);
    peticion.subscribe({
      next: () => {
        this.snack.open(
          this.data.mode === 'create' ? 'Curso creado en estado BORRADOR' : 'Curso actualizado exitosamente', // HU-04 esc. 3
          'OK',
          { duration: 3000 },
        );
        this.dialogRef.close(true);
      },
      error: (err: HttpErrorResponse) => {
        this.guardando.set(false);
        marcarCamposConError(err, this.form);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 });
      },
    });
  }
}
