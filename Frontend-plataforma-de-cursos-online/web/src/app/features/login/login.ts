import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { guardarSesion } from '../../core/sesion';
import { AuthService } from '../../core/services/auth.service';
import { UsuarioService } from '../../core/services/usuario.service';
import { LoginResponse, Rol } from '../../models/api.models';
import { MENSAJE_CAMPOS_OBLIGATORIOS, marcarCampoRepetido, marcarCamposConError, mensajeError } from '../../shared/errores';

/**
 * Login (HU-01): se entra con el correo electrónico (o el nombre de usuario) y la contraseña.
 * Registro (HU-02): el registro público SIEMPRE crea cuentas de estudiante.
 * Solo cuando la base está vacía se crea el primer administrador.
 */
@Component({
  selector: 'app-login',
  imports: [
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class LoginComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly usuarioService = inject(UsuarioService);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly snack = inject(MatSnackBar);

  readonly loading = signal(true);
  readonly hayUsuarios = signal(false); // si no hay ninguno, se crea el primer administrador
  readonly mostrarRegistro = signal(false);
  readonly enviando = signal(false);

  readonly loginForm = this.fb.nonNullable.group({
    nombre_usuario: ['', Validators.required], // correo o nombre de usuario
    contrasena: ['', Validators.required],
  });

  readonly registroForm = this.fb.nonNullable.group({
    nombre_usuario: ['', [Validators.required, Validators.pattern(/^[^@]+$/)]],
    tipo_documento: ['CC', Validators.required],
    documento_identidad: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    contrasena: ['', [Validators.required, Validators.minLength(8)]], // igual que la API (mínimo 8)
    rol: ['Admin' as Rol, Validators.required],
  });

  ngOnInit(): void {
    if (this.route.snapshot.queryParamMap.get('motivo') === 'sesion') {
      this.snack.open('Su sesión terminó. Inicie sesión de nuevo', 'Cerrar', { duration: 5000 });
    }
    this.usuarioService.hayUsuarios().subscribe({
      next: (r) => {
        this.hayUsuarios.set(r.hay_usuarios);
        this.loading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 });
      },
    });
  }

  ingresar(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      this.snack.open(MENSAJE_CAMPOS_OBLIGATORIOS, 'Cerrar', { duration: 4000 });
      return;
    }
    this.enviando.set(true);
    this.authService.login(this.loginForm.getRawValue()).subscribe({
      next: (res) => this.entrar(res),
      // HU-01 esc. 2 y 3: "Credenciales inválidas" o "Su cuenta se encuentra desactivada..."
      error: (err: HttpErrorResponse) => {
        this.enviando.set(false);
        this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 });
      },
    });
  }

  registrarse(): void {
    if (this.registroForm.invalid) {
      this.registroForm.markAllAsTouched();
      this.snack.open(MENSAJE_CAMPOS_OBLIGATORIOS, 'Cerrar', { duration: 4000 }); // HU-02 esc. 3
      return;
    }
    const v = this.registroForm.getRawValue();
    this.enviando.set(true);
    this.usuarioService
      .create({
        ...v,
        // HU-02: si ya hay usuarios el backend siempre crea Estudiante, diga lo que diga aquí
        rol: this.hayUsuarios() ? 'Estudiante' : v.rol,
        activo: true,
      })
      .subscribe({
        // Se inicia sesión de una vez con el rol REAL que asignó el backend
        next: () =>
          this.authService.login({ nombre_usuario: v.email, contrasena: v.contrasena }).subscribe({
            next: (res) => this.entrar(res),
            error: () => {
              this.enviando.set(false);
              this.mostrarRegistro.set(false);
              this.snack.open('Cuenta creada. Inicie sesión con su correo', 'Cerrar', { duration: 5000 });
            },
          }),
        error: (err: HttpErrorResponse) => {
          this.enviando.set(false);
          marcarCamposConError(err, this.registroForm);
          marcarCampoRepetido(err, this.registroForm); // Entregable 3: correo, documento o usuario repetido
          this.snack.open(mensajeError(err), 'Cerrar', { duration: 6000 }); // ej. correo ya registrado (HU-02 esc. 2)
        },
      });
  }

  private entrar(res: LoginResponse): void {
    guardarSesion(res);
    void this.router.navigateByUrl('/app');
  }
}
