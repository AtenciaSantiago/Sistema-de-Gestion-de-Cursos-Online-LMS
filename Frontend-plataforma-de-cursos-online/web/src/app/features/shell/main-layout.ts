import { BreakpointObserver } from '@angular/cdk/layout';
import { AfterViewInit, Component, inject, signal, ViewChild } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSidenav, MatSidenavContainer, MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { rolActual } from '../../core/sesion';
import { AuthService } from '../../core/services/auth.service';
import { Rol } from '../../models/api.models';

const SIDEBAR_KEY = 'shell_sidebar_collapsed';

interface OpcionMenu {
  path: string;
  label: string;
  icon: string;
  roles: Rol[];
}

// Entregable 2: el menú depende del rol (RN-02). Cada ruta también tiene su guarda en app.routes.ts.
const MENU: OpcionMenu[] = [
  // Estudiante: catálogo -> pago -> aula -> evaluación -> certificado
  { path: 'catalogo', label: 'Catálogo', icon: 'storefront', roles: ['Estudiante'] },
  { path: 'mis-cursos', label: 'Mis cursos', icon: 'school', roles: ['Estudiante'] },
  // Docente y Admin: contenido de los cursos
  { path: 'cursos', label: 'Cursos', icon: 'book', roles: ['Admin', 'Docente'] },
  { path: 'categorias', label: 'Categorías', icon: 'category', roles: ['Admin', 'Docente'] },
  { path: 'leccion', label: 'Lecciones', icon: 'library_books', roles: ['Admin', 'Docente'] },
  { path: 'material', label: 'Material', icon: 'description', roles: ['Admin', 'Docente'] },
  { path: 'evaluacion', label: 'Evaluaciones', icon: 'assessment', roles: ['Admin', 'Docente'] },
  { path: 'calificaciones', label: 'Calificaciones', icon: 'star', roles: ['Admin', 'Docente'] },
  // Solo Admin
  { path: 'usuarios', label: 'Usuarios', icon: 'people', roles: ['Admin'] },
  { path: 'inscripciones', label: 'Inscripciones y cierres', icon: 'assignment', roles: ['Admin'] },
  { path: 'pagos', label: 'Pagos', icon: 'payment', roles: ['Admin'] },
  { path: 'certificados', label: 'Certificados', icon: 'workspace_premium', roles: ['Admin'] },
  { path: 'historial', label: 'Historial de cambios', icon: 'history', roles: ['Admin'] },
];

@Component({
  selector: 'app-main-layout',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
  ],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.scss',
})
export class MainLayoutComponent implements AfterViewInit {
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);

  @ViewChild('sidenavShell') private sidenavShell?: MatSidenavContainer;
  @ViewChild('sidenav') private sidenav?: MatSidenav;

  /** RNF-05: en pantallas angostas (celular) el menú va sobre el contenido y arranca cerrado. */
  readonly esMovil = toSignal(
    inject(BreakpointObserver).observe('(max-width: 720px)').pipe(map((r) => r.matches)),
    { initialValue: window.innerWidth <= 720 },
  );

  /** Menú lateral estrecho (solo iconos) o ancho (icono + texto). */
  readonly sidebarCollapsed = signal(localStorage.getItem(SIDEBAR_KEY) === '1');

  readonly rolActual = rolActual() ?? '';
  readonly nombreUsuario = localStorage.getItem('nombre_usuario') ?? '';
  readonly nav = MENU.filter((item) => item.roles.includes(this.rolActual as Rol));

  ngAfterViewInit(): void {
    this.sidenavShell?.updateContentMargins();
  }

  toggleSidebar(): void {
    if (this.esMovil()) {
      void this.sidenav?.toggle(); // en celular el botón abre y cierra el menú completo
      return;
    }
    const siguiente = !this.sidebarCollapsed();
    this.sidebarCollapsed.set(siguiente);
    localStorage.setItem(SIDEBAR_KEY, siguiente ? '1' : '0');
    // Material calcula el margen del contenido según el ancho del menú; se le pide recalcular
    queueMicrotask(() => this.sidenavShell?.updateContentMargins());
    window.setTimeout(() => this.sidenavShell?.updateContentMargins(), 360);
  }

  /** En celular, al elegir una opción el menú se cierra para dejar ver la pantalla. */
  cerrarSiMovil(): void {
    if (this.esMovil()) void this.sidenav?.close();
  }

  logout(): void {
    this.authService.logout();
    void this.router.navigateByUrl('/login');
  }
}
