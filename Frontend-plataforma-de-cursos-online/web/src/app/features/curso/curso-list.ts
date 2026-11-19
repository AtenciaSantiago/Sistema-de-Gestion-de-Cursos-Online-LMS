import { CurrencyPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { filter } from 'rxjs/operators';

import { esAdmin } from '../../core/sesion';
import { CursoService } from '../../core/services/curso.service';
import { CursoResponse, EstadoCurso } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { PAGINADOR_EN_ESPANOL } from '../../shared/paginador-es';
import { CursoDialogComponent, CursoDialogData } from './curso-dialog';
import { CursoEstudiantesDialogComponent } from './curso-estudiantes-dialog';

/** HU-07 esc. 2: mensaje exacto del E1 cuando el docente no tiene cursos asignados. */
const MENSAJE_SIN_CURSOS_DOCENTE =
  'Actualmente no tienes cursos asignados. Contacta al administrador para la asignación de materias';

/**
 * Cursos (HU-04, HU-05, HU-07 y HU-10).
 * - Admin: ve todos, crea asignando profesor, publica u oculta (HU-05).
 * - Docente: solo "Mis cursos asignados" (HU-07); crea cursos que nacen en BORRADOR (HU-04).
 */
@Component({
  selector: 'app-curso-list',
  imports: [
    CurrencyPipe,
    MatTableModule,
    MatPaginatorModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTooltipModule,
  ],
  templateUrl: './curso-list.html',
  providers: [PAGINADOR_EN_ESPANOL],
})
export class CursoListComponent {
  private readonly cursoService = inject(CursoService);
  private readonly dialog = inject(MatDialog);
  private readonly snack = inject(MatSnackBar);
  private readonly router = inject(Router);

  readonly esAdmin = esAdmin();
  readonly mensajeVacio = this.esAdmin ? 'Todavía no hay cursos registrados' : MENSAJE_SIN_CURSOS_DOCENTE;
  readonly titulo = this.esAdmin ? 'Cursos' : 'Mis cursos asignados';

  // HU-07 esc. 1: nombre, categoría, número de lecciones y estado
  readonly displayedColumns = ['nombre_curso', 'nombre_categoria', 'nombre_docente', 'numero_lecciones', 'precio', 'estado_curso', 'acciones'];
  readonly dataSource = new MatTableDataSource<CursoResponse>([]);
  readonly loading = signal(true);

  // La tabla aparece después de cargar; el paginador se conecta apenas existe
  @ViewChild(MatPaginator) set paginator(p: MatPaginator | undefined) {
    if (p) this.dataSource.paginator = p;
  }

  constructor() {
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    this.cursoService.list().subscribe({
      next: (filas) => {
        this.dataSource.data = filas;
        this.loading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 });
      },
    });
  }

  nuevo(): void {
    this.abrirDialogo({ mode: 'create' });
  }

  editar(curso: CursoResponse): void {
    this.abrirDialogo({ mode: 'edit', row: curso });
  }

  /** HU-05 esc. 1 y 2: solo el Admin publica u oculta (pasar a BORRADOR no afecta a los matriculados). */
  cambiarEstado(curso: CursoResponse): void {
    const nuevo: EstadoCurso = curso.estado_curso === 'PUBLICADO' ? 'BORRADOR' : 'PUBLICADO';
    const pregunta =
      nuevo === 'PUBLICADO'
        ? `¿Publicar "${curso.nombre_curso}" en el catálogo?`
        : `¿Ocultar "${curso.nombre_curso}"? Saldrá del catálogo, pero los estudiantes ya matriculados lo seguirán viendo.`;
    if (!confirm(pregunta)) return;

    this.cursoService.update(curso.id_curso, { estado_curso: nuevo }).subscribe({
      next: () => {
        this.snack.open(nuevo === 'PUBLICADO' ? 'Curso publicado' : 'Curso pasado a borrador', 'OK', { duration: 3000 });
        this.reload();
      },
      // HU-05 esc. 3: "El curso debe tener información completa y al menos una lección para ser publicado"
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 7000 }),
    });
  }

  /** HU-07 esc. 3: desde la lista se entra directo al contenido (lecciones) de ese curso. */
  verContenido(curso: CursoResponse): void {
    void this.router.navigate(['/app/leccion'], { queryParams: { curso: curso.id_curso } });
  }

  /** HU-10: estudiantes matriculados en el curso. */
  verEstudiantes(curso: CursoResponse): void {
    // maxWidth: sin él, Angular Material limita el diálogo a 560 px y la columna Estado queda oculta
    this.dialog.open(CursoEstudiantesDialogComponent, { width: '820px', maxWidth: '95vw', data: curso });
  }

  eliminar(curso: CursoResponse): void {
    if (!confirm(`¿Eliminar el curso "${curso.nombre_curso}"?`)) return;
    this.cursoService.delete(curso.id_curso).subscribe({
      next: () => {
        this.snack.open('Curso eliminado', 'OK', { duration: 3000 });
        this.reload();
      },
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 7000 }),
    });
  }

  private abrirDialogo(data: CursoDialogData): void {
    this.dialog
      .open(CursoDialogComponent, { width: '680px', data })
      .afterClosed()
      .pipe(filter(Boolean))
      .subscribe(() => this.reload());
  }
}
