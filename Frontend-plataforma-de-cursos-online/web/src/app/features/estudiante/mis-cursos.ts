import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { EstudianteService } from '../../core/services/estudiante.service';
import { MiCurso } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';

/** HU-12: lista de cursos del estudiante con su estado y % de avance. */
@Component({
  selector: 'app-mis-cursos',
  imports: [RouterLink, MatButtonModule, MatCardModule, MatIconModule, MatProgressBarModule, MatProgressSpinnerModule],
  templateUrl: './mis-cursos.html',
  styleUrl: './estudiante.scss',
})
export class MisCursosComponent implements OnInit {
  private readonly estudianteService = inject(EstudianteService);

  readonly cursos = signal<MiCurso[]>([]);
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.estudianteService.misCursos().subscribe({
      next: (c) => {
        this.cursos.set(c);
        this.cargando.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.error.set(mensajeError(err));
        this.cargando.set(false);
      },
    });
  }

  /** Solo con inscripción ACTIVA, APROBADA o REPROBADA se puede entrar (HU-12 escenario 4). */
  puedeEntrar(c: MiCurso): boolean {
    return ['ACTIVA', 'APROBADA', 'REPROBADA'].includes(c.estado_inscripcion);
  }
}
