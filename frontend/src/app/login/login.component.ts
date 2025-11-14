import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  imports: [CommonModule, FormsModule],
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
