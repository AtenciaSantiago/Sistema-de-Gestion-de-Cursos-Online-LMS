import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { forkJoin } from 'rxjs';
import { filter } from 'rxjs/operators';

import { CursoService } from '../../core/services/curso.service';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { LeccionService } from '../../core/services/leccion.service';
import { CursoResponse, EvaluacionResponse, LeccionResponse } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { EvaluacionDialogComponent, EvaluacionDialogData } from './evaluacion-dialog';
import { PreguntasDialogComponent } from './preguntas-dialog';

/** Una fila = una lección del curso con su evaluación (RN-03: una evaluación por lección). */
interface FilaEvaluacion {
  leccion: LeccionResponse;
  evaluacion: EvaluacionResponse | null;
}

/**
 * HU-14: evaluaciones de un curso. Cada una tiene su porcentaje (los del curso suman máximo 100)
 * y su nota mínima para aprobar (0 a 5). Las preguntas se arman con la Factory del backend.
 */
@Component({
  selector: 'app-evaluacion-list',
  imports: [
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatFormFieldModule,
    MatSelectModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTooltipModule,
  ],
  templateUrl: './evaluacion-list.html',
})
export class EvaluacionListComponent {
  private readonly evaluacionService = inject(EvaluacionService);
  private readonly leccionService = inject(LeccionService);
  private readonly dialog = inject(MatDialog);
  private readonly snack = inject(MatSnackBar);
  private readonly router = inject(Router);

  readonly cursos = signal<CursoResponse[]>([]);
  readonly idCurso = signal(inject(ActivatedRoute).snapshot.queryParamMap.get('curso') ?? '');
  readonly filas = signal<FilaEvaluacion[]>([]);
  readonly loading = signal(false);
  readonly displayedColumns = ['leccion', 'nombre_evaluacion', 'porcentaje', 'nota_minima', 'acciones'];

  /** Suma de los porcentajes del curso (el backend no deja pasar de 100). */
  readonly sumaPorcentajes = computed(() => this.filas().reduce((s, f) => s + (f.evaluacion?.porcentaje ?? 0), 0));

  constructor() {
    inject(CursoService).list().subscribe({
      next: (c) => {
        this.cursos.set(c);
        if (!this.idCurso() && c.length === 1) this.idCurso.set(c[0].id_curso);
        this.reload();
      },
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }),
    });
  }

  escogerCurso(id: string): void {
    this.idCurso.set(id);
    void this.router.navigate([], { queryParams: { curso: id }, replaceUrl: true });
    this.reload();
  }

  reload(): void {
    if (!this.idCurso()) return;
    this.loading.set(true);
    forkJoin({ lecciones: this.leccionService.list(this.idCurso()), evaluaciones: this.evaluacionService.list() }).subscribe({
      next: ({ lecciones, evaluaciones }) => {
        this.filas.set(
          lecciones.map((leccion) => ({
            leccion,
            evaluacion: evaluaciones.find((e) => e.id_leccion === leccion.id_leccion) ?? null,
          })),
        );
        this.loading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 });
      },
    });
  }

  crear(fila: FilaEvaluacion): void {
    this.abrir({ mode: 'create', leccion: fila.leccion, disponible: 100 - this.sumaPorcentajes() });
  }

  editar(fila: FilaEvaluacion): void {
    this.abrir({
      mode: 'edit',
      leccion: fila.leccion,
      row: fila.evaluacion!,
      disponible: 100 - this.sumaPorcentajes() + fila.evaluacion!.porcentaje,
    });
  }

  preguntas(fila: FilaEvaluacion): void {
    this.dialog.open(PreguntasDialogComponent, { width: '760px', data: fila.evaluacion });
  }

  eliminar(fila: FilaEvaluacion): void {
    if (!confirm(`¿Eliminar la evaluación "${fila.evaluacion!.nombre_evaluacion}" y sus preguntas?`)) return;
    this.evaluacionService.delete(fila.evaluacion!.id_evaluacion).subscribe({
      next: () => {
        this.snack.open('Evaluación eliminada', 'OK', { duration: 3000 });
        this.reload();
      },
      // HU-14 esc. 2: si ya la presentaron, no se puede
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }),
    });
  }

  private abrir(data: EvaluacionDialogData): void {
    this.dialog
      .open(EvaluacionDialogComponent, { width: '560px', data })
      .afterClosed()
      .pipe(filter(Boolean))
      .subscribe(() => this.reload());
  }
}
