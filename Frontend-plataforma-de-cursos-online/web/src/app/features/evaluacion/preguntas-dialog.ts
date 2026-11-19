import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { EvaluacionService } from '../../core/services/evaluacion.service';
import { PreguntaService } from '../../core/services/pregunta.service';
import { EvaluacionResponse, PreguntaDocente, TipoPregunta } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';

/**
 * HU-14: el docente arma las preguntas de una evaluación.
 * Aquí solo se escoge el TIPO; en el backend el patrón Factory Method decide cómo
 * construir y validar cada tipo (por ejemplo, que la clave esté entre las opciones).
 * HU-14 esc. 2: si algún estudiante ya la presentó, se muestra en solo lectura.
 */
@Component({
  selector: 'app-preguntas-dialog',
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
    MatSnackBarModule,
    MatTooltipModule,
  ],
  templateUrl: './preguntas-dialog.html',
  styles: `
    .pregunta { display: flex; gap: 8px; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid var(--mat-sys-outline-variant); }
    .pregunta > div { flex: 1; }
    .detalle { font-size: 13px; color: var(--mat-sys-on-surface-variant); }
    form { display: grid; gap: 8px; }
    h3 { margin-top: 20px; }
  `,
})
export class PreguntasDialogComponent {
  private readonly fb = inject(FormBuilder);
  private readonly preguntaService = inject(PreguntaService);
  private readonly snack = inject(MatSnackBar);
  readonly evaluacion = inject<EvaluacionResponse>(MAT_DIALOG_DATA);

  readonly preguntas = signal<PreguntaDocente[]>([]);
  // Arranca en false y solo pasa a true cuando la API confirma que se puede editar: así el
  // formulario no aparece y desaparece (parpadeo) en una evaluación ya presentada (HU-14 esc. 2).
  readonly editable = signal(false);
  readonly permisoConsultado = signal(false);
  readonly motivoNoEditable = signal<string | null>(null);
  readonly editando = signal<PreguntaDocente | null>(null); // null = agregando una nueva

  readonly form = this.fb.nonNullable.group({
    tipo: ['OPCION_MULTIPLE' as TipoPregunta, Validators.required],
    enunciado: ['', Validators.required],
    opcionesTexto: [''], // una opción por línea (solo opción múltiple)
    respuesta_correcta: ['', Validators.required],
  });

  constructor() {
    inject(EvaluacionService).editable(this.evaluacion.id_evaluacion).subscribe({
      next: (r) => {
        this.editable.set(r.editable);
        this.motivoNoEditable.set(r.mensaje); // "La evaluación ya fue presentada por estudiantes..."
        this.permisoConsultado.set(true);
      },
      error: () => this.permisoConsultado.set(true),
    });
    this.cargar();
  }

  /** Opciones escritas por el docente, una por línea. En verdadero/falso siempre son las mismas. */
  opciones(): string[] {
    if (this.form.controls.tipo.value === 'VERDADERO_FALSO') return ['Verdadero', 'Falso'];
    return this.form.controls.opcionesTexto.value
      .split('\n')
      .map((o) => o.trim())
      .filter(Boolean);
  }

  editar(p: PreguntaDocente): void {
    this.editando.set(p);
    this.form.reset({
      tipo: p.tipo,
      enunciado: p.enunciado,
      opcionesTexto: p.tipo === 'OPCION_MULTIPLE' ? p.opciones.join('\n') : '',
      respuesta_correcta: p.respuesta_correcta,
    });
  }

  cancelarEdicion(): void {
    this.editando.set(null);
    this.form.reset({ tipo: this.form.controls.tipo.value, enunciado: '', opcionesTexto: '', respuesta_correcta: '' });
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      // HU-14 esc. 3
      this.snack.open('Debe seleccionar la respuesta correcta y definir una nota de aprobación válida', 'Cerrar', { duration: 5000 });
      return;
    }
    const v = this.form.getRawValue();
    const datos = { tipo: v.tipo, enunciado: v.enunciado, opciones: this.opciones(), respuesta_correcta: v.respuesta_correcta };
    const actual = this.editando();
    const peticion = actual
      ? this.preguntaService.actualizar(actual.id_pregunta, datos)
      : this.preguntaService.crear(this.evaluacion.id_evaluacion, datos);

    peticion.subscribe({
      next: () => {
        this.snack.open(actual ? 'Pregunta actualizada' : 'Pregunta agregada', 'OK', { duration: 2500 });
        this.cancelarEdicion();
        this.cargar();
      },
      // Si la Factory la rechaza (ej. la clave no está entre las opciones) se muestra el motivo
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }),
    });
  }

  eliminar(p: PreguntaDocente): void {
    if (!confirm('¿Eliminar esta pregunta?')) return;
    this.preguntaService.eliminar(p.id_pregunta).subscribe({
      next: () => this.cargar(),
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }),
    });
  }

  private cargar(): void {
    this.preguntaService.listarConClave(this.evaluacion.id_evaluacion).subscribe({
      next: (p) => this.preguntas.set(p),
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }),
    });
  }
}
