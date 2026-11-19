import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal, ViewChild } from '@angular/core';
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
import { CategoriaService } from '../../core/services/categoria.service';
import { CategoriaResponse } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { PAGINADOR_EN_ESPANOL } from '../../shared/paginador-es';
import { CategoriaDialogComponent, CategoriaDialogData } from './categoria-dialog';

/**
 * HU-04 esc. 1: categorías de los cursos.
 * El Admin o el Docente pueden crear; editar y eliminar solo el Admin (afecta los cursos de todos).
 */
@Component({
  selector: 'app-categoria-list',
  imports: [
    DatePipe,
    MatTableModule,
    MatPaginatorModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTooltipModule,
  ],
  templateUrl: './categoria-list.html',
  providers: [PAGINADOR_EN_ESPANOL],
})
export class CategoriaListComponent {
  private readonly svc = inject(CategoriaService);
  private readonly dialog = inject(MatDialog);
  private readonly snack = inject(MatSnackBar);

  readonly esAdmin = esAdmin();
  readonly displayedColumns = this.esAdmin
    ? ['nombre_categoria', 'fecha_creacion', 'acciones']
    : ['nombre_categoria', 'fecha_creacion'];
  readonly dataSource = new MatTableDataSource<CategoriaResponse>([]);
  readonly loading = signal(true);

  @ViewChild(MatPaginator) set paginator(p: MatPaginator | undefined) {
    if (p) this.dataSource.paginator = p;
  }

  constructor() {
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    this.svc.list().subscribe({
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
    this.abrir({ mode: 'create' });
  }

  editar(categoria: CategoriaResponse): void {
    this.abrir({ mode: 'edit', row: categoria });
  }

  eliminar(categoria: CategoriaResponse): void {
    if (!confirm(`¿Eliminar la categoría "${categoria.nombre_categoria}"?`)) return;
    this.svc.delete(categoria.id_categoria).subscribe({
      next: () => {
        this.snack.open('Categoría eliminada', 'OK', { duration: 3000 });
        this.reload();
      },
      // Si tiene cursos: "No se puede eliminar la categoría porque tiene cursos asociados"
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }),
    });
  }

  private abrir(data: CategoriaDialogData): void {
    this.dialog
      .open(CategoriaDialogComponent, { width: '480px', data })
      .afterClosed()
      .pipe(filter(Boolean))
      .subscribe(() => this.reload());
  }
}
