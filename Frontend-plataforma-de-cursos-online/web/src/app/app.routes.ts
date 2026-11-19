import { Routes } from '@angular/router';

import { inicioSegunRol, rolGuard, sesionGuard } from './core/guards';

// Entregable 2: cada pantalla dice qué rol la puede abrir (RN-02). El backend igual lo vuelve a revisar.
const SOLO_ADMIN = rolGuard('Admin');
const ADMIN_O_DOCENTE = rolGuard('Admin', 'Docente');
const SOLO_ESTUDIANTE = rolGuard('Estudiante');

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', loadComponent: () => import('./features/login/login').then((m) => m.LoginComponent) },

  {
    path: 'app',
    canActivate: [sesionGuard],
    loadComponent: () => import('./features/shell/main-layout').then((m) => m.MainLayoutComponent),
    children: [
      // El estudiante entra al catálogo; docente y admin a cursos
      { path: '', pathMatch: 'full', redirectTo: () => inicioSegunRol() },

      // ===== Estudiante: catálogo -> pago -> aula -> evaluación -> certificado =====
      {
        path: 'catalogo', // HU-06 y HU-09
        canActivate: [SOLO_ESTUDIANTE],
        loadComponent: () => import('./features/estudiante/catalogo').then((m) => m.CatalogoComponent),
      },
      {
        path: 'mis-cursos', // HU-12
        canActivate: [SOLO_ESTUDIANTE],
        loadComponent: () => import('./features/estudiante/mis-cursos').then((m) => m.MisCursosComponent),
      },
      {
        path: 'mis-cursos/:idCurso', // HU-12, HU-13 y HU-16
        canActivate: [SOLO_ESTUDIANTE],
        loadComponent: () => import('./features/estudiante/aula').then((m) => m.AulaComponent),
      },
      {
        path: 'mis-cursos/:idCurso/evaluacion/:idEvaluacion', // HU-15
        canActivate: [SOLO_ESTUDIANTE],
        loadComponent: () => import('./features/estudiante/quiz').then((m) => m.QuizComponent),
      },

      // ===== Docente y Admin: contenido de los cursos =====
      {
        path: 'cursos', // HU-04, HU-05, HU-07 y HU-10
        canActivate: [ADMIN_O_DOCENTE],
        loadComponent: () => import('./features/curso/curso-list').then((m) => m.CursoListComponent),
      },
      {
        path: 'categorias', // HU-04 esc. 1
        canActivate: [ADMIN_O_DOCENTE],
        loadComponent: () => import('./features/categoria/categoria-list').then((m) => m.CategoriaListComponent),
      },
      {
        path: 'leccion', // HU-11
        canActivate: [ADMIN_O_DOCENTE],
        loadComponent: () => import('./features/leccion/leccion-list').then((m) => m.LeccionListComponent),
      },
      {
        path: 'material', // HU-11 esc. 2
        canActivate: [ADMIN_O_DOCENTE],
        loadComponent: () => import('./features/material/material-list').then((m) => m.MaterialListComponent),
      },
      {
        path: 'evaluacion', // HU-14
        canActivate: [ADMIN_O_DOCENTE],
        loadComponent: () => import('./features/evaluacion/evaluacion-list').then((m) => m.EvaluacionListComponent),
      },
      {
        path: 'calificaciones', // RF-03 (solo lectura)
        canActivate: [ADMIN_O_DOCENTE],
        loadComponent: () => import('./features/calificacion/calificacion-list').then((m) => m.CalificacionListComponent),
      },

      // ===== Solo Admin =====
      {
        path: 'usuarios', // HU-03
        canActivate: [SOLO_ADMIN],
        loadComponent: () => import('./features/usuarios/usuario-list').then((m) => m.UsuarioListComponent),
      },
      {
        path: 'inscripciones', // RF-10 y HU-17
        canActivate: [SOLO_ADMIN],
        loadComponent: () => import('./features/inscripcion/inscripcion-list').then((m) => m.InscripcionListComponent),
      },
      {
        path: 'pagos', // RF-11 (solo lectura)
        canActivate: [SOLO_ADMIN],
        loadComponent: () => import('./features/pago/pago-list').then((m) => m.PagoListComponent),
      },
      {
        path: 'certificados', // HU-13 / RF-16 (solo lectura)
        canActivate: [SOLO_ADMIN],
        loadComponent: () => import('./features/certificado/certificado-list').then((m) => m.CertificadoListComponent),
      },
      {
        path: 'historial', // RF-07 control de cambios (solo lectura)
        canActivate: [SOLO_ADMIN],
        loadComponent: () => import('./features/historial/historial-list').then((m) => m.HistorialListComponent),
      },
    ],
  },

  { path: '**', redirectTo: 'login' },
];
