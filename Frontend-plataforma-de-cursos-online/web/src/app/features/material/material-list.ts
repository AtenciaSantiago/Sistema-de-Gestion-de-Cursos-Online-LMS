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
import { filter } from 'rxjs/operators';

import { CursoService } from '../../core/services/curso.service';
import { LeccionService } from '../../core/services/leccion.service';
import { MaterialService } from '../../core/services/material.service';
import { CursoResponse, LeccionResponse, MaterialResponse } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { MaterialDialogComponent, MaterialDialogData } from './material-dialog';

/**
 * HU-11 esc. 2: materiales de una lección (PDF, video, documento o enlace).
 * RN-03: todo material pertenece a una lección; por eso primero se escoge curso y lección.
 */
@Component({
  selector: 'app-material-list',
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
  templateUrl: './material-list.html',
})
export class MaterialListComponent {
  private readonly materialService = inject(MaterialService);
  private readonly leccionService = inject(LeccionService);
  private readonly dialog = inject(MatDialog);
  private readonly snack = inject(MatSnackBar);
  private readonly router = inject(Router);

  readonly cursos = signal<CursoResponse[]>([]);
  readonly lecciones = signal<LeccionResponse[]>([]);
  readonly materiales = signal<MaterialResponse[]>([]);
  readonly idCurso = signal('');
  readonly idLeccion = signal('');
  readonly loading = signal(false);
  readonly displayedColumns = ['titulo_material', 'tipo_material', 'URL_archivo', 'acciones'];

  constructor() {
    const params = inject(ActivatedRoute).snapshot.queryParamMap;
    this.idCurso.set(params.get('curso') ?? '');
    this.idLeccion.set(params.get('leccion') ?? '');

    inject(CursoService).list().subscribe({
      next: (c) => {
        this.cursos.set(c);
        if (this.idCurso()) this.cargarLecciones();
      },
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }),
    });
  }

  escogerCurso(id: string): void {
    this.idCurso.set(id);
    this.idLeccion.set('');
    this.materiales.set([]);
    this.actualizarUrl();
    this.cargarLecciones();
  }

  escogerLeccion(id: string): void {
    this.idLeccion.set(id);
    this.actualizarUrl();
    this.reload();
  }

  private cargarLecciones(): void {
    this.leccionService.list(this.idCurso()).subscribe({
      next: (l) => {
        this.lecciones.set(l);
        if (this.idLeccion()) this.reload();
      },
    });
  }

  reload(): void {
    if (!this.idLeccion()) return;
    this.loading.set(true);
    this.materialService.list(this.idLeccion()).subscribe({
      next: (filas) => {
        this.materiales.set(filas);
        this.loading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 });
      },
    });
  }

  nuevo(): void {
    this.abrir({ mode: 'create', idLeccion: this.idLeccion() });
  }

  editar(material: MaterialResponse): void {
    this.abrir({ mode: 'edit', idLeccion: this.idLeccion(), row: material });
  }

  eliminar(material: MaterialResponse): void {
    if (!confirm(`¿Eliminar el material "${material.titulo_material}"?`)) return;
    this.materialService.delete(material.id_material).subscribe({
      next: () => {
        this.snack.open('Material eliminado', 'OK', { duration: 3000 });
        this.reload();
      },
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }),
    });
  }

  private actualizarUrl(): void {
    void this.router.navigate([], {
      queryParams: { curso: this.idCurso() || null, leccion: this.idLeccion() || null },
      replaceUrl: true,
    });
  }

  private abrir(data: MaterialDialogData): void {
    this.dialog
      .open(MaterialDialogComponent, { width: '560px', data })
      .afterClosed()
      .pipe(filter(Boolean))
      .subscribe(() => this.reload());
  }
}
