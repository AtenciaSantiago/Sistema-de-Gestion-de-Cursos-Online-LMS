import { CurrencyPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { CategoriaService } from '../../core/services/categoria.service';
import { EstudianteService } from '../../core/services/estudiante.service';
import { CategoriaResponse, CursoResponse, EstadoInscripcion } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { CheckoutDialogComponent } from './checkout-dialog';

/** HU-06 esc. 3: mensaje exacto del E1 cuando la categoría no tiene cursos publicados. */
const MENSAJE_SIN_CURSOS = 'No se encontraron cursos disponibles para la categoría seleccionada';

/**
 * HU-06 Catálogo: el estudiante ve los cursos PUBLICADOS y los filtra por categoría.
 * Desde aquí arranca la compra (HU-09). Si ya está inscrito, se le lleva a su curso.
 */
@Component({
  selector: 'app-catalogo',
  imports: [
    CurrencyPipe,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatDialogModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './catalogo.html',
  styleUrl: './estudiante.scss',
})
export class CatalogoComponent implements OnInit {
  private readonly estudianteService = inject(EstudianteService);
  private readonly categoriaService = inject(CategoriaService);
  private readonly dialog = inject(MatDialog);
  private readonly router = inject(Router);
  private readonly snack = inject(MatSnackBar);

  readonly mensajeSinCursos = MENSAJE_SIN_CURSOS;
  readonly cursos = signal<CursoResponse[]>([]);
  readonly categorias = signal<CategoriaResponse[]>([]);
  readonly categoriaActiva = signal<string | null>(null);
  readonly cargando = signal(true);
  /** Estado de mi inscripción en cada curso (para no ofrecer comprar dos veces). */
  readonly misEstados = signal<Record<string, EstadoInscripcion>>({});

  ngOnInit(): void {
    this.categoriaService.list().subscribe({ next: (c) => this.categorias.set(c) });
    this.estudianteService.misCursos().subscribe({
      next: (mios) => this.misEstados.set(Object.fromEntries(mios.map((m) => [m.id_curso, m.estado_inscripcion]))),
    });
    this.cargar();
  }

  filtrar(idCategoria: string | null): void {
    this.categoriaActiva.set(idCategoria);
    this.cargar();
  }

  /** ACTIVA, APROBADA o REPROBADA: ya tiene el curso (PENDIENTE o CANCELADA sí puede pagar). */
  yaLoTiene(curso: CursoResponse): boolean {
    const estado = this.misEstados()[curso.id_curso];
    return estado === 'ACTIVA' || estado === 'APROBADA' || estado === 'REPROBADA';
  }

  irAlCurso(curso: CursoResponse): void {
    void this.router.navigate(['/app/mis-cursos', curso.id_curso]);
  }

  comprar(curso: CursoResponse): void {
    this.dialog
      .open(CheckoutDialogComponent, { data: curso, width: '520px' })
      .afterClosed()
      .subscribe((pagado) => {
        // Si el pago se aprobó, la inscripción ya está ACTIVA (RN-01): lo llevamos a su aula
        if (pagado) this.irAlCurso(curso);
      });
  }

  private cargar(): void {
    this.cargando.set(true);
    this.estudianteService.catalogo(this.categoriaActiva() ?? undefined).subscribe({
      next: (c) => {
        this.cursos.set(c);
        this.cargando.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.cargando.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 });
      },
    });
  }
}
