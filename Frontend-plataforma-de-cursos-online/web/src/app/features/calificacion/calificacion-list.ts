import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal, ViewChild } from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';

import { CalificacionService } from '../../core/services/calificacion.service';
import { CalificacionResponse } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { PAGINADOR_EN_ESPANOL } from '../../shared/paginador-es';

/**
 * RF-03: consulta de calificaciones (Admin: todas; Docente: las de sus cursos).
 * Entregable 2: es de SOLO LECTURA. Las notas las calcula el sistema cuando el estudiante
 * presenta (HU-15) y cada intento queda guardado (RF-13); nadie las sube ni las baja a mano.
 */
@Component({
  selector: 'app-calificacion-list',
  imports: [
    DatePipe,
    DecimalPipe,
    MatTableModule,
    MatPaginatorModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './calificacion-list.html',
  providers: [PAGINADOR_EN_ESPANOL],
})
export class CalificacionListComponent {
  private readonly svc = inject(CalificacionService);
  private readonly snack = inject(MatSnackBar);

  readonly displayedColumns = ['nombre_estudiante', 'nombre_curso', 'nombre_evaluacion', 'Nota', 'fecha'];
  readonly dataSource = new MatTableDataSource<CalificacionResponse>([]);
  readonly loading = signal(true);

  @ViewChild(MatPaginator) set paginator(p: MatPaginator | undefined) {
    if (p) this.dataSource.paginator = p;
  }

  constructor() {
    // El buscador revisa estudiante, curso y evaluación
    this.dataSource.filterPredicate = (c, texto) =>
      [c.nombre_estudiante, c.nombre_curso, c.nombre_evaluacion].join(' ').toLowerCase().includes(texto);

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

  buscar(texto: string): void {
    this.dataSource.filter = texto.trim().toLowerCase();
  }
}
