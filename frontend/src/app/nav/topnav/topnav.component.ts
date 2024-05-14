import { Component, Renderer2 } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-topnav',
  standalone: true,
  imports: [RouterLink, FormsModule],
  templateUrl: './topnav.component.html',
  styleUrl: './topnav.component.css'
})
export class TopnavComponent {
  isDarkModeEnabled = true;
  constructor(private renderer: Renderer2) { }
  
  // Check theme preference on page load and apply it
  ngOnInit() {
    // Check if theme is already set in local storage
    const theme = localStorage.getItem('theme');
    if (theme) {
      this.isDarkModeEnabled = theme === 'dark';
      this.renderer.setAttribute(document.documentElement, 'theme', theme);
      this.renderer.addClass(document.body, theme);
      console.log('LocalStorage: %s mode enabled', theme);
    } else {
      // Check if the user prefers dark mode
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        // The user has indicated that they prefer a dark color scheme
        this.isDarkModeEnabled = true;
        this.renderer.setAttribute(document.documentElement, 'theme', 'dark');
        this.renderer.addClass(document.body, 'dark');
        localStorage.setItem('theme', 'dark');
        console.log('Media: Dark mode enabled');
      } else {
        // The user has indicated that they prefer a light color scheme
        this.isDarkModeEnabled = false;
        this.renderer.setAttribute(document.documentElement, 'theme', 'light');
        this.renderer.addClass(document.body, 'light');
        localStorage.setItem('theme', 'light');
        console.log('Media: Light mode enabled');
      }
    }
  }
  count = 0;
  onThemeChange(event: any) {
    let theme = '';
    let oldTheme = '';
    if (event) {
      oldTheme = 'light';
      theme = 'dark';
    } else {
      oldTheme = 'dark';
      theme = 'light';
    }
    this.renderer.setAttribute(document.documentElement, 'theme', theme);
    this.renderer.removeClass(document.body, oldTheme);
    this.renderer.addClass(document.body, theme);
    localStorage.setItem('theme', theme);
    console.log('Event: %s, Count: %d', event, this.count);
    this.count++;
    return;
  }
  searchQuery = '';
  onSearch() {
    console.log('Search query: %s', this.searchQuery);
    this.searchQuery = '';
    // throw new Error('Method not implemented.');
  }
}
