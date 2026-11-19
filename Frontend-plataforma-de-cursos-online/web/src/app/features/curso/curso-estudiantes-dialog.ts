import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';

import { CursoService } from '../../core/services/curso.service';
import { CursoResponse, ReporteEstudiantes } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';

/**
 * HU-10: el profesor ve los estudiantes matriculados en su curso (ACTIVA, y también los que ya
 * cerraron: APROBADA o REPROBADA): nombre, correo, fecha de inscripción, avance y estado.
 */
@Component({
  selector: 'app-curso-estudiantes-dialog',
  imports: [DatePipe, MatDialogModule, MatButtonModule, MatIconModule, MatTableModule, MatProgressBarModule, MatProgressSpinnerModule],
  template: `
    <h2 mat-dialog-title>Estudiantes matriculados · {{ curso.nombre_curso }}</h2>
    <mat-dialog-content>
      @if (cargando()) {
        <div class="loading"><mat-spinner diameter="40" /></div>
      } @else if (error()) {
        <p>{{ error() }}</p>
      } @else if (reporte()?.mensaje) {
        <!-- HU-10 esc. 2 -->
        <div class="vacio">
          <mat-icon>person_off</mat-icon>
          <p>{{ reporte()!.mensaje }}</p>
        </div>
      } @else {
        <table mat-table [dataSource]="reporte()!.estudiantes">
          <ng-container matColumnDef="nombre">
            <th mat-header-cell *matHeaderCellDef>Nombre</th>
            <td mat-cell *matCellDef="let e">{{ e.nombre_estudiante }}</td>
          </ng-container>
          <ng-container matColumnDef="email">
            <th mat-header-cell *matHeaderCellDef>Correo</th>
            <td mat-cell *matCellDef="let e">{{ e.email }}</td>
          </ng-container>
          <ng-container matColumnDef="fecha">
            <th mat-header-cell *matHeaderCellDef>Inscripción</th>
            <td mat-cell *matCellDef="let e">{{ e.fecha_inscripcion | date: 'dd/MM/yyyy' }}</td>
          </ng-container>
          <ng-container matColumnDef="avance">
            <th mat-header-cell *matHeaderCellDef>Avance</th>
            <td mat-cell *matCellDef="let e" class="avance">
              <mat-progress-bar mode="determinate" [value]="e.porcentaje_avance" />
              <span>{{ e.porcentaje_avance }} %</span>
            </td>
          </ng-container>
          <ng-container matColumnDef="estado">
            <th mat-header-cell *matHeaderCellDef>Estado</th>
            <td mat-cell *matCellDef="let e"><span class="estado" [class]="e.estado_inscripcion">{{ e.estado_inscripcion }}</span></td>
          </ng-container>
          <tr mat-header-row *matHeaderRowDef="columnas"></tr>
          <tr mat-row *matRowDef="let fila; columns: columnas"></tr>
        </table>
      }
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close type="button">Cerrar</button>
    </mat-dialog-actions>
  `,
  styles: `
    table { width: 100%; }
    .avance { display: flex; align-items: center; gap: 8px; min-width: 140px; }
    .avance span { white-space: nowrap; }
  `,
})
export class CursoEstudiantesDialogComponent {
  private readonly cursoService = inject(CursoService);
  readonly curso = inject<CursoResponse>(MAT_DIALOG_DATA);

  readonly columnas = ['nombre', 'email', 'fecha', 'avance', 'estado'];
  readonly cargando = signal(true);
  readonly reporte = signal<ReporteEstudiantes | null>(null);
  readonly error = signal<string | null>(null);

  constructor() {
    this.cursoService.estudiantes(this.curso.id_curso).subscribe({
      next: (r) => {
        this.reporte.set(r);
        this.cargando.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.error.set(mensajeError(err));
        this.cargando.set(false);
      },
    });
  }
}
