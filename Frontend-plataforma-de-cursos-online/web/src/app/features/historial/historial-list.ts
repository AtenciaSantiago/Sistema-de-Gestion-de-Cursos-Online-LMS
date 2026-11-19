import { DatePipe } from '@angular/common';
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

import { HistorialService } from '../../core/services/historial.service';
import { UsuarioService } from '../../core/services/usuario.service';
import { HistorialCambioResponse, UsuarioResponse } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { PAGINADOR_EN_ESPANOL } from '../../shared/paginador-es';

/**
 * RF-07 Control de cambios (problema P7 del modelo verbal): historial de modificaciones de
 * contenidos activos (solo Admin, solo lectura). Cada fila dice quién, cuándo y qué cambió.
 */
@Component({
  selector: 'app-historial-list',
  imports: [
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
  templateUrl: './historial-list.html',
  providers: [PAGINADOR_EN_ESPANOL],
})
export class HistorialListComponent {
  private readonly historialService = inject(HistorialService);
  private readonly usuarioService = inject(UsuarioService);
  private readonly snack = inject(MatSnackBar);
  private readonly fb = inject(FormBuilder);

  readonly entidades = [
    { valor: 'CURSO', texto: 'Cursos' },
    { valor: 'LECCION', texto: 'Lecciones' },
    { valor: 'MATERIAL', texto: 'Materiales' },
    { valor: 'EVALUACION', texto: 'Evaluaciones' },
    { valor: 'PREGUNTA', texto: 'Preguntas' },
    { valor: 'CATEGORIA', texto: 'Categorías' },
  ];
  readonly displayedColumns = ['fecha', 'nombre_usuario', 'entidad', 'nombre_registro', 'accion', 'detalle'];
  readonly dataSource = new MatTableDataSource<HistorialCambioResponse>([]);
  readonly loading = signal(true);
  readonly usuarios = signal<UsuarioResponse[]>([]);

  readonly filtro = this.fb.nonNullable.group({ entidad: '', id_usuario: '', desde: '', hasta: '' });

  @ViewChild(MatPaginator) set paginator(p: MatPaginator | undefined) {
    if (p) this.dataSource.paginator = p;
  }

  constructor() {
    // Solo editan contenidos el Admin y los docentes (RN-02)
    this.usuarioService.list().subscribe({ next: (u) => this.usuarios.set(u.filter((x) => x.rol !== 'Estudiante')) });
    this.buscar();
  }

  buscar(): void {
    this.loading.set(true);
    this.historialService.list(this.filtro.getRawValue()).subscribe({
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

  limpiar(): void {
    this.filtro.reset();
    this.buscar();
  }

  textoEntidad(valor: string): string {
    return this.entidades.find((e) => e.valor === valor)?.texto ?? valor;
  }
}
