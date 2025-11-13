import { Component } from '@angular/core';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  username = '';
  password = '';

  constructor(private authService: AuthService) { }

  login(): void {
    const credentials = {
      username: this.username,
      password: this.password
    };
    this.authService.login(credentials).subscribe({
      next: () => {
        window.location.reload();
      },
      error: (error) => {
        console.error('Login failed', error);
      }
    });
  }
}
