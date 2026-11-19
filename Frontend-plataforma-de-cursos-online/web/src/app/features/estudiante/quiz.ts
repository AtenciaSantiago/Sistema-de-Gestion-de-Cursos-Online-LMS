import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatRadioModule } from '@angular/material/radio';

import { EstudianteService } from '../../core/services/estudiante.service';
import { MiResultado, PreguntaEstudiante, ResultadoEvaluacion } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';

/**
 * HU-15: el estudiante responde la evaluación y el sistema la califica solo.
 * Las preguntas pueden ser de opción múltiple o verdadero/falso (en el backend las crea
 * el patrón Factory Method); aquí todas se muestran igual: enunciado + opciones.
 * Si era la última evaluación, el backend cierra el curso (patrón Observer).
 * Esc. 3: si ya la aprobó (o el curso ya cerró) se muestra su resultado en solo lectura.
 */
@Component({
  selector: 'app-quiz',
  imports: [DatePipe, FormsModule, RouterLink, MatButtonModule, MatCardModule, MatIconModule, MatProgressSpinnerModule, MatRadioModule],
  templateUrl: './quiz.html',
  styleUrl: './estudiante.scss',
})
export class QuizComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly estudianteService = inject(EstudianteService);

  readonly cargando = signal(true);
  readonly preguntas = signal<PreguntaEstudiante[]>([]);
  readonly anterior = signal<MiResultado | null>(null); // resultado en solo lectura
  readonly resultado = signal<ResultadoEvaluacion | null>(null); // lo que acaba de presentar
  readonly error = signal<string | null>(null);
  readonly enviando = signal(false);
  respuestas: Record<string, string> = {};

  idCurso = '';
  private idEvaluacion = '';

  ngOnInit(): void {
    this.idCurso = this.route.snapshot.paramMap.get('idCurso') ?? '';
    this.idEvaluacion = this.route.snapshot.paramMap.get('idEvaluacion') ?? '';

    // Primero se mira si ya la había presentado
    this.estudianteService.miResultado(this.idEvaluacion).subscribe({
      next: (r) => {
        if (!r.puede_presentar) {
          this.anterior.set(r); // HU-15 esc. 3: solo lectura
          this.cargando.set(false);
        } else {
          this.anterior.set(r.intentos.length ? r : null); // intentos anteriores, si perdió
          this.cargarPreguntas();
        }
      },
      error: (err: HttpErrorResponse) => this.fallo(err),
    });
  }

  completo(): boolean {
    return this.preguntas().every((p) => !!this.respuestas[p.id_pregunta]);
  }

  enviar(): void {
    this.enviando.set(true);
    this.estudianteService.presentar(this.idEvaluacion, this.respuestas).subscribe({
      next: (r) => {
        this.resultado.set(r);
        this.enviando.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.enviando.set(false);
        this.fallo(err);
      },
    });
  }

  private cargarPreguntas(): void {
    this.estudianteService.preguntas(this.idEvaluacion).subscribe({
      next: (p) => {
        this.preguntas.set(p);
        if (p.length === 0) this.error.set('Esta evaluación todavía no tiene preguntas. Consulte a su profesor');
        this.cargando.set(false);
      },
      error: (err: HttpErrorResponse) => this.fallo(err),
    });
  }

  private fallo(err: HttpErrorResponse): void {
    this.error.set(mensajeError(err));
    this.cargando.set(false);
  }
}
