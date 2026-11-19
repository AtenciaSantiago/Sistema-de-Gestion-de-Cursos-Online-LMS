import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal, ViewChild } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { filter } from 'rxjs/operators';

import { idUsuarioActual } from '../../core/sesion';
import { UsuarioService } from '../../core/services/usuario.service';
import { UsuarioResponse } from '../../models/api.models';
import { mensajeError } from '../../shared/errores';
import { PAGINADOR_EN_ESPANOL } from '../../shared/paginador-es';
import { UsuarioDialogComponent, UsuarioDialogData } from './usuario-dialog';

/** HU-03: el Admin crea cuentas, cambia roles y activa o desactiva usuarios. */
@Component({
  selector: 'app-usuario-list',
  imports: [
    DatePipe,
    MatTableModule,
    MatPaginatorModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTooltipModule,
  ],
  templateUrl: './usuario-list.html',
  providers: [PAGINADOR_EN_ESPANOL],
})
export class UsuarioListComponent {
  private readonly usuarioService = inject(UsuarioService);
  private readonly dialog = inject(MatDialog);
  private readonly snack = inject(MatSnackBar);

  /** El admin no se puede desactivar ni borrar a sí mismo (la plataforma se quedaría sin administrador). */
  readonly miId = idUsuarioActual();
  readonly displayedColumns = ['nombre_usuario', 'email', 'rol', 'activo', 'fecha_creacion', 'acciones'];
  readonly dataSource = new MatTableDataSource<UsuarioResponse>([]);
  readonly loading = signal(true);

  @ViewChild(MatPaginator) set paginator(p: MatPaginator | undefined) {
    if (p) this.dataSource.paginator = p;
  }

  constructor() {
    this.dataSource.filterPredicate = (u, texto) => [u.nombre_usuario, u.email, u.rol].join(' ').toLowerCase().includes(texto);
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    this.usuarioService.list().subscribe({
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

  buscar(texto: string): void {
    this.dataSource.filter = texto.trim().toLowerCase();
  }

  nuevo(): void {
    this.abrir({ mode: 'create' });
  }

  editar(usuario: UsuarioResponse): void {
    this.abrir({ mode: 'edit', row: usuario });
  }

  /** HU-03 esc. 3: al desactivarlo pierde el acceso de inmediato (aunque tenga la sesión abierta). */
  cambiarActivo(usuario: UsuarioResponse): void {
    const accion = usuario.activo ? 'Desactivar' : 'Activar';
    if (!confirm(`¿${accion} la cuenta de ${usuario.nombre_usuario}?`)) return;
    this.usuarioService.update(usuario.id_usuario, { activo: !usuario.activo }).subscribe({
      next: () => {
        this.snack.open(usuario.activo ? 'Cuenta desactivada' : 'Cuenta activada', 'OK', { duration: 3000 });
        this.reload();
      },
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }),
    });
  }

  eliminar(usuario: UsuarioResponse): void {
    if (!confirm(`¿Eliminar el usuario ${usuario.nombre_usuario}?`)) return;
    this.usuarioService.delete(usuario.id_usuario).subscribe({
      next: () => {
        this.snack.open('Usuario eliminado', 'OK', { duration: 3000 });
        this.reload();
      },
      // Si tiene cursos, pagos o inscripciones: se sugiere desactivarlo en vez de borrarlo
      error: (err: HttpErrorResponse) => this.snack.open(mensajeError(err), 'Cerrar', { duration: 7000 }),
    });
  }

  private abrir(data: UsuarioDialogData): void {
    this.dialog
      .open(UsuarioDialogComponent, { width: '560px', data })
      .afterClosed()
      .pipe(filter(Boolean))
      .subscribe(() => this.reload());
  }
}
