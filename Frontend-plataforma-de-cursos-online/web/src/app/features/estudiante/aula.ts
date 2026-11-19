import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { EstudianteService } from '../../core/services/estudiante.service';
import { ContenidoCurso, LeccionAula } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';

/**
 * Aula virtual (HU-12): lecciones en orden, materiales, "Marcar como completada"
 * y el % de avance. Desde aquí se presenta la evaluación (HU-15) y, cuando el
 * curso queda APROBADO, se descarga el certificado (HU-13). Mientras no, el botón
 * se ve deshabilitado con el mensaje del E1 (HU-13 esc. 2 y 3).
 */
/** "Diseño de interfaces" -> "Diseno-de-interfaces": sin tildes ni eñes, que algunos navegadores rechazan en nombres de archivo. */
function nombreDeArchivo(texto: string): string {
  return texto
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^A-Za-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

@Component({
  selector: 'app-aula',
  imports: [
    RouterLink,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatListModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './aula.html',
  styleUrl: './estudiante.scss',
})
export class AulaComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly estudianteService = inject(EstudianteService);
  private readonly snack = inject(MatSnackBar);

  readonly contenido = signal<ContenidoCurso | null>(null);
  readonly seleccionada = signal<LeccionAula | null>(null);
  readonly error = signal<string | null>(null);
  /** Después del cierre (APROBADA o REPROBADA) el curso queda en solo lectura. */
  readonly activa = computed(() => this.contenido()?.estado_inscripcion === 'ACTIVA');

  private idCurso = '';

  ngOnInit(): void {
    this.idCurso = this.route.snapshot.paramMap.get('idCurso') ?? '';
    this.cargar();
  }

  seleccionar(leccion: LeccionAula): void {
    this.seleccionada.set(leccion);
  }

  marcarCompletada(leccion: LeccionAula): void {
    this.estudianteService.marcarCompletada(leccion.id_leccion).subscribe({
      next: (r) => {
        this.snack.open(`${r.mensaje} · Avance ${r.porcentaje_avance} %`, 'Cerrar', { duration: r.estado_curso ? 6000 : 3000 });
        this.cargar(leccion.id_leccion);
      },
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 5000 }),
    });
  }

  descargarCertificado(): void {
    this.estudianteService.certificado(this.idCurso).subscribe({
      next: (pdf) => {
        const url = URL.createObjectURL(pdf);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = `certificado-${nombreDeArchivo(this.contenido()?.nombre_curso ?? 'curso')}.pdf`;
        // El enlace se pone en la página para que todos los navegadores respeten el nombre del archivo
        document.body.appendChild(enlace);
        enlace.click();
        enlace.remove();
        // Se libera el archivo temporal un momento después, para no cortar la descarga
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      },
      error: () =>
        this.snack.open(this.contenido()?.mensaje_certificado ?? 'No se pudo descargar el certificado', 'Cerrar', { duration: 5000 }),
    });
  }

  private cargar(mantenerLeccion?: string): void {
    this.estudianteService.contenido(this.idCurso).subscribe({
      next: (c) => {
        this.contenido.set(c);
        const elegida = c.lecciones.find((l) => l.id_leccion === mantenerLeccion)
          ?? c.lecciones.find((l) => !l.completada)
          ?? c.lecciones[0]
          ?? null;
        this.seleccionada.set(elegida);
      },
      // HU-12 esc. 4: "No cuenta con una inscripción activa para visualizar este contenido"
      error: (err: HttpErrorResponse) => this.error.set(mensajeError(err)),
    });
  }
}
