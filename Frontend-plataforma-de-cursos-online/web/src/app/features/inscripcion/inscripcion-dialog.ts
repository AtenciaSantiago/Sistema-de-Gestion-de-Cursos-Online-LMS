import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { CursoService } from '../../core/services/curso.service';
import { InscripcionService } from '../../core/services/inscripcion.service';
import { UsuarioService } from '../../core/services/usuario.service';
import { CursoResponse, UsuarioResponse } from '../../models/api.models';
import { MENSAJE_CAMPOS_OBLIGATORIOS, mensajeError } from '../../shared/errores';

/**
 * RF-10: matrícula manual del Admin (por ejemplo, una beca). La inscripción queda ACTIVA.
 * Entregable 2: aquí ya no se escoge el estado; lo cambian solo el pago (HU-09) y el cierre (HU-16).
 */
@Component({
  selector: 'app-inscripcion-dialog',
  imports: [ReactiveFormsModule, MatDialogModule, MatButtonModule, MatFormFieldModule, MatSelectModule, MatSnackBarModule],
  template: `
    <h2 mat-dialog-title>Matrícula manual</h2>
    <mat-dialog-content class="dialog-body">
      <p class="aviso-solo-lectura">La inscripción queda ACTIVA sin pago (por ejemplo, una beca).</p>
      <form [formGroup]="form" class="grid">
        <mat-form-field appearance="outline" class="span-2">
          <mat-label>Curso publicado</mat-label>
          <mat-select formControlName="id_curso" required>
            @for (c of cursos(); track c.id_curso) {
              <mat-option [value]="c.id_curso">{{ c.nombre_curso }}</mat-option>
            }
          </mat-select>
          <mat-error>Campo obligatorio</mat-error>
        </mat-form-field>
        <mat-form-field appearance="outline" class="span-2">
          <mat-label>Estudiante</mat-label>
          <mat-select formControlName="id_usuario_inscrito" required>
            @for (e of estudiantes(); track e.id_usuario) {
              <mat-option [value]="e.id_usuario">{{ e.nombre_usuario }} · {{ e.email }}</mat-option>
            }
          </mat-select>
          <mat-error>Campo obligatorio</mat-error>
        </mat-form-field>
      </form>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button type="button" mat-dialog-close>Cancelar</button>
      <button mat-flat-button color="primary" type="button" (click)="matricular()" [disabled]="guardando()">Matricular</button>
    </mat-dialog-actions>
  `,
})
export class InscripcionDialogComponent {
  private readonly fb = inject(FormBuilder);
  private readonly inscripcionService = inject(InscripcionService);
  private readonly dialogRef = inject(MatDialogRef<InscripcionDialogComponent, boolean>);
  private readonly snack = inject(MatSnackBar);

  readonly cursos = signal<CursoResponse[]>([]);
  readonly estudiantes = signal<UsuarioResponse[]>([]);
  readonly guardando = signal(false);

  readonly form = this.fb.nonNullable.group({
    id_curso: ['', Validators.required],
    id_usuario_inscrito: ['', Validators.required],
  });

  constructor() {
    inject(CursoService).list().subscribe({ next: (c) => this.cursos.set(c.filter((x) => x.estado_curso === 'PUBLICADO')) });
    inject(UsuarioService).list().subscribe({
      next: (u) => this.estudiantes.set(u.filter((x) => x.rol === 'Estudiante' && x.activo)),
    });
  }

  matricular(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.snack.open(MENSAJE_CAMPOS_OBLIGATORIOS, 'Cerrar', { duration: 4000 });
      return;
    }
    this.guardando.set(true);
    this.inscripcionService.matricular(this.form.getRawValue()).subscribe({
      next: () => this.dialogRef.close(true),
      error: (err: HttpErrorResponse) => {
        this.guardando.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }); // ej. ya tiene inscripción
      },
    });
  }
}
