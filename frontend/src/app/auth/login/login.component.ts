import {ChangeDetectionStrategy, Component, computed, inject, OnInit, signal} from '@angular/core';
import {Router} from '@angular/router';
import {AuthService} from '../../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginComponent implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  protected username = signal('');
  protected password = signal('');
  protected errorMessage = signal('');
  protected isLoading = signal(false);
  protected isSubmitDisabled = computed(() => this.isLoading() || !this.username().trim() || !this.password().trim());

  ngOnInit(): void {
    // If already authenticated, go straight to home
    this.authService.checkAuthStatus().subscribe((authenticated) => {
      if (authenticated) {
        this.router.navigate(['/home']);
      }
    });
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    const u = this.username();
    const p = this.password();
    if (!u || !p) {
      this.errorMessage.set('Username and password are required.');
      return;
    }
    this.isLoading.set(true);
    this.errorMessage.set('');
    this.authService.login(u, p).subscribe({
      next: () => {
        const params = new URLSearchParams(window.location.search);
        const returnUrl = params.get('returnUrl') || '/home';
        window.location.href = returnUrl;
      },
      error: () => {
        this.isLoading.set(false);
        this.errorMessage.set('Invalid username or password.');
      },
    });
  }
}
