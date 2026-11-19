import { CurrencyPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { EstudianteService } from '../../core/services/estudiante.service';
import { CheckoutRequest, CheckoutResponse, CursoResponse } from '../../models/api.models';
import { MENSAJE_CAMPOS_OBLIGATORIOS, mensajeError } from '../../shared/errores';

/**
 * HU-09 Pago en línea. El estudiante elige TARJETA o PSE (en el backend cada medio
 * es una estrategia del patrón Strategy) y la pasarela simulada responde
 * (patrón Adapter). Si se aprueba, la inscripción queda ACTIVA sola.
 */
@Component({
  selector: 'app-checkout-dialog',
  imports: [
    CurrencyPipe,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
  ],
  templateUrl: './checkout-dialog.html',
  styleUrl: './estudiante.scss',
})
export class CheckoutDialogComponent {
  private readonly fb = inject(FormBuilder);
  private readonly estudianteService = inject(EstudianteService);
  private readonly dialogRef = inject(MatDialogRef<CheckoutDialogComponent, boolean>);
  readonly curso = inject<CursoResponse>(MAT_DIALOG_DATA);

  readonly bancos = ['BANCOLOMBIA', 'DAVIVIENDA', 'BANCO DE BOGOTÁ', 'NEQUI'];
  readonly metodo = signal<'TARJETA' | 'PSE'>('TARJETA');
  readonly procesando = signal(false);
  readonly resultado = signal<CheckoutResponse | null>(null);
  readonly error = signal<string | null>(null);

  readonly tarjeta = this.fb.nonNullable.group({
    numero_tarjeta: ['', [Validators.required, Validators.pattern(/^(\d{4} ?){3}\d{4}$/)]],
    titular: ['', Validators.required],
  });

  readonly pse = this.fb.nonNullable.group({
    banco: ['', Validators.required],
    tipo_persona: ['NATURAL' as 'NATURAL' | 'JURIDICA', Validators.required],
  });

  pagar(): void {
    const form = this.metodo() === 'TARJETA' ? this.tarjeta : this.pse;
    if (form.invalid) {
      form.markAllAsTouched();
      this.error.set(this.mensajeFormulario());
      return;
    }
    const body: CheckoutRequest = { metodo_pago: this.metodo(), ...form.getRawValue() };
    this.procesando.set(true);
    this.error.set(null);
    this.estudianteService.pagarCurso(this.curso.id_curso, body).subscribe({
      next: (r) => {
        this.resultado.set(r);
        this.procesando.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.error.set(mensajeError(err)); // ej. "Ya te encuentras matriculado activamente en este curso"
        this.procesando.set(false);
      },
    });
  }

  /**
   * Entregable 3: el mensaje dice qué dato está mal, con las mismas frases de la API
   * (src/patrones/pagos.py), en lugar del genérico de campos obligatorios.
   */
  private mensajeFormulario(): string {
    if (this.metodo() === 'TARJETA') {
      const numero = this.tarjeta.controls.numero_tarjeta;
      if (numero.value.trim() && numero.hasError('pattern')) {
        return 'El número de tarjeta debe tener 16 dígitos';
      }
      if (numero.valid && this.tarjeta.controls.titular.invalid) {
        return 'Debe escribir el nombre del titular';
      }
    } else if (this.pse.controls.banco.invalid) {
      return 'Debe seleccionar un banco';
    }
    return MENSAJE_CAMPOS_OBLIGATORIOS;
  }

  /** HU-09 esc. 2: si la pasarela rechaza, puede intentar otra vez (con otro medio de pago). */
  reintentar(): void {
    this.resultado.set(null);
    this.error.set(null);
  }

  cerrar(): void {
    this.dialogRef.close(this.resultado()?.aprobado ?? false);
  }
}
