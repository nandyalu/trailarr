import { NgFor, NgIf } from '@angular/common';
import { Component, ElementRef, HostListener, Renderer2 } from '@angular/core';
import { FormControl, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { SearchMedia } from '../../models/media';
import { SearchService } from '../../services/search.service';

@Component({
  selector: 'app-topnav',
  standalone: true,
  imports: [RouterLink, FormsModule, ReactiveFormsModule, NgIf, NgFor, RouterLink],
  templateUrl: './topnav.component.html',
  styleUrl: './topnav.component.css'
})
export class TopnavComponent {
  isDarkModeEnabled = true;
  searchQuery = '';
  searchForm = new FormControl();
  searchResults: SearchMedia[] = [];
  selectedIndex = -1;
  selectedId = -1;
  constructor(
    private renderer: Renderer2,
    private searchService: SearchService,
    private elementRef: ElementRef,
    private router: Router,
  ) {
    this.searchForm.valueChanges
      .pipe(
        debounceTime(400),
        distinctUntilChanged()
      )
      .subscribe((value) => {
        // console.log('Search query: %s', value);
        this.onSearch(value);
      });
  }

  @HostListener('document:click', ['$event'])
  clickout(event: Event) {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.searchResults = [];
      this.selectedId = -1;
      this.selectedIndex = -1;
    }
  }

  @HostListener('document:mousemove', ['$event'])
  disableSelection(event: Event) {
    if (this.searchResults.length > 0) {
      this.selectedId = -1;
      this.selectedIndex = -1;
    }
  }

  @HostListener('document:keydown', ['$event'])
  handleKeyboardEvent(event: KeyboardEvent) {
    if (event.ctrlKey && event.key === 'f') {
      event.preventDefault();  // Prevent the browser's default Ctrl+F behavior
      const searchInput = document.getElementById('searchForm')?.querySelector('input');
      searchInput?.focus();  // Focus the search input field
      return;
    }
    if (this.searchResults.length > 0) {
      if (event.key === 'Escape') {
        this.searchResults = [];
        this.selectedId = -1;
        this.selectedIndex = -1;
        return;
      }
      let firstId = this.searchResults[0].id;
      let lastId = this.searchResults[this.searchResults.length - 1].id;
      if (event.key === 'ArrowDown' || event.key === 'Tab' && !event.shiftKey) {
        event.preventDefault();
        // If the last item is selected, loop back to the first item
        if (this.selectedId === lastId) {
          this.selectedIndex = 0;
          this.selectedId = firstId;
          return;
        }
        // Else, select the next item
        this.selectedIndex = this.selectedIndex + 1;
        this.selectedId = this.searchResults[this.selectedIndex].id;
        return;
      } else if (event.key === 'ArrowUp' || (event.shiftKey && event.key === 'Tab')) {
        event.preventDefault();
        // If the first item is selected, loop back to the last item
        if (this.selectedId === firstId) {
          this.selectedIndex = this.searchResults.length - 1;
          this.selectedId = lastId;
          return;
        }
        // Else, select the previous item
        this.selectedIndex = this.selectedIndex - 1;
        this.selectedId = this.searchResults[this.selectedIndex].id;
        return;
      } else if (event.key === 'Enter') {
        const selectedResult = this.searchResults[this.selectedIndex];
        this.router.navigate([selectedResult.is_movie ? 'movies' : 'series', this.selectedId]);
        this.searchResults = [];
        return;
      }
    }
  }

  // Check theme preference on page load and apply it
  ngOnInit() {
    // Check if theme is already set in local storage
    const theme = localStorage.getItem('theme');
    if (theme) {
      let darkTheme = theme === 'dark';
      this.setTheme(darkTheme);
      // console.log('LocalStorage: %s mode enabled', theme);
    } else {
      // Check if the user prefers dark mode
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        // The user has indicated that they prefer a dark color scheme
        this.setTheme(true);
        // console.log('Media: Dark mode enabled');
      } else {
        // The user has indicated that they prefer a light color scheme
        this.setTheme(false);
        // console.log('Media: Light mode enabled');
      }
    }
  }
  onThemeChange(event: any) {
    // if (event) {
    //   this.setTheme(true);
    // } else {
    //   this.setTheme(false);
    // }
    this.setTheme(event ? true : false);
    // let darkTheme = event.target.checked;
    // this.setTheme(darkTheme);
    return;
  }

  setTheme(darkTheme: boolean = true) {
    let theme = darkTheme ? 'dark' : 'light';
    let oldTheme = darkTheme ? 'light' : 'dark';
    this.isDarkModeEnabled = darkTheme;
    this.renderer.setAttribute(document.documentElement, 'theme', theme);
    this.renderer.removeClass(document.body, oldTheme);
    this.renderer.addClass(document.body, theme);
    localStorage.setItem('theme', theme);
    // console.log('Theme set to %s', theme);
    return;
  }


  onSearch(query: string = '') {
    if (query.length < 3) {
      this.searchResults = [];
      return;
    }
    if (query.trim() === this.searchQuery) {
      return;
    }
    this.searchQuery = query;
    // console.log('Search query: %s', this.searchQuery);
    this.searchService.searchMedia(this.searchQuery).subscribe((media_list: SearchMedia[]) => {
      // console.log('Search results: %o', media_list);
      this.searchResults = media_list;
    });
  }
}
