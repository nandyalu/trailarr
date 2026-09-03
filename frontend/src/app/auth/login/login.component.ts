import {Location} from '@angular/common';
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
  private readonly location = inject(Location);

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
        // prepareExternalUrl adds the base href. Without it the app goes to the
        // server root, and a URL base (reverse proxy setup) is lost.
        window.location.href = this.location.prepareExternalUrl(returnUrl);
      },
      error: (err: {status?: number}) => {
        this.isLoading.set(false);
        // A network failure (status 0) or a gateway error means the server is
        // not reachable, not that the password is wrong. Reporting those as
        // bad credentials sends people looking for the wrong fix.
        const status = err?.status;
        const unreachable = status === 0 || status === 502 || status === 503 || status === 504;
        this.errorMessage.set(
          unreachable ? 'Cannot reach the Trailarr server. Check that it is running.' : 'Invalid username or password.',
        );
      },
    });
  }
}
