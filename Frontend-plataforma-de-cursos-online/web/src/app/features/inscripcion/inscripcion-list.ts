import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal, ViewChild } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Observable } from 'rxjs';
import { filter } from 'rxjs/operators';

import { InscripcionService } from '../../core/services/inscripcion.service';
import { InscripcionResponse } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { PAGINADOR_EN_ESPANOL } from '../../shared/paginador-es';
import { InscripcionDialogComponent } from './inscripcion-dialog';

type Vista = 'todas' | 'cierres';

/**
 * Inscripciones (solo Admin).
 * - RF-10: matrícula manual y cancelación. El Admin NUNCA aprueba ni reprueba: eso lo hace el sistema.
 * - HU-17: auditoría de cierres académicos (APROBADA, REPROBADA, FINALIZADA) con promedio y código del certificado.
 */
@Component({
  selector: 'app-inscripcion-list',
  imports: [
    DatePipe,
    DecimalPipe,
    MatTableModule,
    MatPaginatorModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatFormFieldModule,
    MatSelectModule,
    MatIconModule,
    MatDialogModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTooltipModule,
  ],
  templateUrl: './inscripcion-list.html',
  providers: [PAGINADOR_EN_ESPANOL],
})
export class InscripcionListComponent {
  private readonly inscripcionService = inject(InscripcionService);
  private readonly dialog = inject(MatDialog);
  private readonly snack = inject(MatSnackBar);

  readonly vista = signal<Vista>('todas');
  readonly estado = signal('');
  readonly loading = signal(true);
  readonly dataSource = new MatTableDataSource<InscripcionResponse>([]);

  readonly columnasTodas = ['nombre_estudiante', 'nombre_curso', 'estado_inscripcion', 'fecha_creacion', 'acciones'];
  readonly columnasCierres = ['nombre_estudiante', 'nombre_curso', 'estado_inscripcion', 'promedio_final', 'codigo_certificado', 'fecha_edicion'];
  readonly estadosTodas = ['PENDIENTE', 'ACTIVA', 'CANCELADA', 'APROBADA', 'REPROBADA'];
  readonly estadosCierre = ['APROBADA', 'REPROBADA', 'FINALIZADA'];

  @ViewChild(MatPaginator) set paginator(p: MatPaginator | undefined) {
    if (p) this.dataSource.paginator = p;
  }

  constructor() {
    this.reload();
  }

  cambiarVista(vista: Vista): void {
    this.vista.set(vista);
    this.estado.set('');
    this.reload();
  }

  /** HU-17: texto de la tabla vacía según la vista y el filtro elegido. */
  mensajeVacio(): string {
    if (this.vista() !== 'cierres') {
      return 'No hay inscripciones con ese filtro';
    }
    return this.estado() ? `No hay cierres académicos con el estado ${this.estado()}` : 'Todavía no hay cursos cerrados';
  }

  filtrar(estado: string): void {
    this.estado.set(estado);
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    const peticion: Observable<InscripcionResponse[]> =
      this.vista() === 'cierres'
        ? this.inscripcionService.cierres(this.estado()) // HU-17 esc. 1 y 2
        : this.inscripcionService.list(this.estado());
    peticion.subscribe({
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

  matricular(): void {
    this.dialog
      .open(InscripcionDialogComponent, { width: '520px' })
      .afterClosed()
      .pipe(filter(Boolean))
      .subscribe(() => {
        this.snack.open('Estudiante matriculado (inscripción ACTIVA)', 'OK', { duration: 3000 });
        this.reload();
      });
  }

  puedeCancelarse(i: InscripcionResponse): boolean {
    return i.estado_inscripcion === 'PENDIENTE' || i.estado_inscripcion === 'ACTIVA';
  }

  /** RF-10: por solicitud o por mora. El estudiante pierde el acceso al contenido (RF-09). */
  cancelar(i: InscripcionResponse): void {
    if (!confirm(`¿Cancelar la inscripción de ${i.nombre_estudiante} en "${i.nombre_curso}"? Perderá el acceso al curso.`)) return;
    this.inscripcionService.cancelar(i.id_inscripcion).subscribe({
      next: () => {
        this.snack.open('Inscripción cancelada', 'OK', { duration: 3000 });
        this.reload();
      },
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }),
    });
  }
}
