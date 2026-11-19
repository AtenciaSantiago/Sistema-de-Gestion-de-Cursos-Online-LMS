import { CurrencyPipe, DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal, ViewChild } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';

import { CursoService } from '../../core/services/curso.service';
import { PagoService } from '../../core/services/pago.service';
import { UsuarioService } from '../../core/services/usuario.service';
import { CursoResponse, PagoResponse, UsuarioResponse } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { PAGINADOR_EN_ESPANOL } from '../../shared/paginador-es';

/**
 * RF-11: auditoría de pagos (solo Admin, solo lectura).
 * Los pagos los registra el sistema en el checkout (HU-09), aprobados o rechazados.
 * Se filtran por curso, estudiante y rango de fechas.
 */
@Component({
  selector: 'app-pago-list',
  imports: [
    CurrencyPipe,
    DatePipe,
    ReactiveFormsModule,
    MatTableModule,
    MatPaginatorModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './pago-list.html',
  providers: [PAGINADOR_EN_ESPANOL],
})
export class PagoListComponent {
  private readonly pagoService = inject(PagoService);
  private readonly cursoService = inject(CursoService);
  private readonly usuarioService = inject(UsuarioService);
  private readonly snack = inject(MatSnackBar);
  private readonly fb = inject(FormBuilder);

  readonly displayedColumns = ['fecha', 'nombre_estudiante', 'nombre_curso', 'metodo_pago', 'monto', 'estado_pago', 'referencia'];
  readonly dataSource = new MatTableDataSource<PagoResponse>([]);
  readonly loading = signal(true);
  readonly cursos = signal<CursoResponse[]>([]);
  readonly estudiantes = signal<UsuarioResponse[]>([]);

  readonly filtro = this.fb.nonNullable.group({ id_curso: '', id_estudiante: '', desde: '', hasta: '' });

  @ViewChild(MatPaginator) set paginator(p: MatPaginator | undefined) {
    if (p) this.dataSource.paginator = p;
  }

  constructor() {
    this.cursoService.list().subscribe({ next: (c) => this.cursos.set(c) });
    this.usuarioService.list().subscribe({ next: (u) => this.estudiantes.set(u.filter((x) => x.rol === 'Estudiante')) });
    this.buscar();
  }

  buscar(): void {
    this.loading.set(true);
    this.pagoService.list(this.filtro.getRawValue()).subscribe({
      next: (filas) => {
        this.dataSource.data = filas;
        this.loading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }); // ej. fecha inicial mayor que la final
      },
    });
  }

  limpiar(): void {
    this.filtro.reset();
    this.buscar();
  }
}
