import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
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
import { concat, lastValueFrom } from 'rxjs';
import { filter } from 'rxjs/operators';

import { CursoService } from '../../core/services/curso.service';
import { LeccionService } from '../../core/services/leccion.service';
import { CursoResponse, LeccionResponse } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { LeccionDialogComponent, LeccionDialogData } from './leccion-dialog';

/**
 * HU-11: el profesor arma la ruta de aprendizaje de UN curso: crea lecciones con su número
 * de orden (esc. 1), las reordena (esc. 3) y desde aquí pasa a sus materiales (esc. 2).
 * Se llega desde "Mis cursos asignados" con ?curso=... (HU-07 esc. 3).
 */
@Component({
  selector: 'app-leccion-list',
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
  templateUrl: './leccion-list.html',
})
export class LeccionListComponent {
  private readonly leccionService = inject(LeccionService);
  private readonly cursoService = inject(CursoService);
  private readonly dialog = inject(MatDialog);
  private readonly snack = inject(MatSnackBar);
  private readonly router = inject(Router);

  readonly cursos = signal<CursoResponse[]>([]);
  readonly idCurso = signal<string>(inject(ActivatedRoute).snapshot.queryParamMap.get('curso') ?? '');
  readonly lecciones = signal<LeccionResponse[]>([]);
  readonly loading = signal(false);
  readonly moviendo = signal(false);
  readonly displayedColumns = ['orden', 'titulo_leccion', 'duracion_horas', 'acciones'];

  constructor() {
    this.cursoService.list().subscribe({
      next: (c) => {
        this.cursos.set(c);
        // Si no venía un curso escogido y solo hay uno, se abre ese
        if (!this.idCurso() && c.length === 1) this.idCurso.set(c[0].id_curso);
        this.reload();
      },
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }),
    });
  }

  cursoActual(): CursoResponse | undefined {
    return this.cursos().find((c) => c.id_curso === this.idCurso());
  }

  escogerCurso(id: string): void {
    this.idCurso.set(id);
    void this.router.navigate([], { queryParams: { curso: id }, replaceUrl: true });
    this.reload();
  }

  reload(): void {
    if (!this.idCurso()) {
      this.lecciones.set([]);
      return;
    }
    this.loading.set(true);
    this.leccionService.list(this.idCurso()).subscribe({
      next: (filas) => {
        this.lecciones.set(filas); // ya vienen ordenadas por "orden"
        this.loading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 });
      },
    });
  }

  nueva(): void {
    const siguiente = Math.max(0, ...this.lecciones().map((l) => l.orden)) + 1;
    this.abrir({ mode: 'create', idCurso: this.idCurso(), ordenSugerido: siguiente });
  }

  editar(leccion: LeccionResponse): void {
    this.abrir({ mode: 'edit', idCurso: this.idCurso(), row: leccion });
  }

  /**
   * HU-11 esc. 3: subir o bajar una lección intercambia su número con la de al lado.
   * Como el orden no se puede repetir dentro del curso, se usa un número libre de paso.
   */
  async mover(indice: number, direccion: -1 | 1): Promise<void> {
    const lista = this.lecciones();
    const a = lista[indice];
    const b = lista[indice + direccion];
    if (!a || !b) return;
    const libre = Math.max(...lista.map((l) => l.orden)) + 1;

    this.moviendo.set(true);
    try {
      await lastValueFrom(
        concat(
          this.leccionService.update(a.id_leccion, { orden: libre }),
          this.leccionService.update(b.id_leccion, { orden: a.orden }),
          this.leccionService.update(a.id_leccion, { orden: b.orden }),
        ),
      );
      this.snack.open('Orden actualizado', 'OK', { duration: 2000 });
    } catch (err) {
      this.snack.open(mensajeError(err as HttpErrorResponse), 'Cerrar', { duration: 6000 });
    }
    this.moviendo.set(false);
    this.reload();
  }

  verMateriales(leccion: LeccionResponse): void {
    void this.router.navigate(['/app/material'], { queryParams: { curso: this.idCurso(), leccion: leccion.id_leccion } });
  }

  eliminar(leccion: LeccionResponse): void {
    if (!confirm(`¿Eliminar la lección "${leccion.titulo_leccion}"?`)) return;
    this.leccionService.delete(leccion.id_leccion).subscribe({
      next: () => {
        this.snack.open('Lección eliminada', 'OK', { duration: 3000 });
        this.reload();
      },
      // ej. tiene materiales o evaluación, o es la única de un curso publicado
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 7000 }),
    });
  }

  private abrir(data: LeccionDialogData): void {
    this.dialog
      .open(LeccionDialogComponent, { width: '560px', data })
      .afterClosed()
      .pipe(filter(Boolean))
      .subscribe(() => this.reload());
  }
}
