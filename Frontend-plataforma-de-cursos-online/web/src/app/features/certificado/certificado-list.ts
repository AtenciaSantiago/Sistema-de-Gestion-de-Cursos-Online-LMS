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

import { CertificadoService } from '../../core/services/certificado.service';
import { CertificadoResponse } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { PAGINADOR_EN_ESPANOL } from '../../shared/paginador-es';

/**
 * HU-13 / RF-16: certificados emitidos (solo Admin, solo lectura).
 * Los emite el sistema al aprobar el curso (Observer, HU-16). Un certificado emitido
 * es inalterable: no se edita ni se borra. Cualquiera lo verifica con su código (RF-17).
 */
@Component({
  selector: 'app-certificado-list',
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
  templateUrl: './certificado-list.html',
  providers: [PAGINADOR_EN_ESPANOL],
})
export class CertificadoListComponent {
  private readonly svc = inject(CertificadoService);
  private readonly snack = inject(MatSnackBar);

  readonly displayedColumns = ['codigo_verificacion', 'nombre_estudiante', 'nombre_curso', 'promedio_final', 'fecha_creacion'];
  readonly dataSource = new MatTableDataSource<CertificadoResponse>([]);
  readonly loading = signal(true);

  @ViewChild(MatPaginator) set paginator(p: MatPaginator | undefined) {
    if (p) this.dataSource.paginator = p;
  }

  constructor() {
    this.dataSource.filterPredicate = (c, texto) =>
      [c.codigo_verificacion, c.nombre_estudiante, c.nombre_curso].join(' ').toLowerCase().includes(texto);

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
