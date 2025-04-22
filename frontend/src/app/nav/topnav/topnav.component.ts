import {NgFor, NgIf} from '@angular/common';
import {Component, DestroyRef, ElementRef, HostListener, inject, OnInit, Renderer2} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import {debounceTime, distinctUntilChanged} from 'rxjs/operators';
import {RouteHome, RouteMedia} from 'src/routing';
import {SearchMedia} from '../../models/media';
import {MediaService} from '../../services/media.service';

@Component({
  selector: 'app-topnav',
  imports: [RouterLink, FormsModule, ReactiveFormsModule, NgIf, NgFor, RouterLink],
  templateUrl: './topnav.component.html',
  styleUrl: './topnav.component.scss',
})
export class TopnavComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  private readonly elementRef = inject(ElementRef);
  private readonly mediaService = inject(MediaService);
  private readonly renderer = inject(Renderer2);
  private readonly router = inject(Router);

  isDarkModeEnabled = true;
  searchQuery = '';
  searchForm = new FormControl();
  searchResults: SearchMedia[] = [];
  selectedIndex = -1;
  selectedId = -1;

  protected readonly RouteHome = RouteHome;

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
    const activeElement = document.activeElement as HTMLElement;

    // Check if the active element is an input, textarea, or contenteditable element
    const isInputField = activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.isContentEditable;

    // Only handle the 'f' key if the active element is not an input field
    if (!isInputField && event.key === 'f') {
      // if (event.ctrlKey && event.key === 'f') {
      event.preventDefault(); // Prevent the browser's default behavior
      const searchInput = document.getElementById('searchForm')?.querySelector('input');
      searchInput?.focus(); // Focus the search input field
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
      if (event.key === 'ArrowDown' || (event.key === 'Tab' && !event.shiftKey)) {
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
        // const selectedResult = this.searchResults[this.selectedIndex];
        this.router.navigate([RouteMedia, this.selectedId]);
        this.searchResults = [];
        return;
      }
    }
  }

  // Check theme preference on page load and apply it
  ngOnInit() {
    this.searchForm.valueChanges.pipe(debounceTime(400), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef)).subscribe((value) => {
      // console.log('Search query: %s', value);
      this.onSearch(value);
    });

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

  noSearchResult: SearchMedia = {
    id: -1,
    title: 'No results found',
    imdb_id: '',
    txdb_id: '',
    poster_path: '',
    year: 0,
    youtube_trailer_id: '',
    is_movie: true,
  };
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
    this.mediaService.searchMedia(this.searchQuery).subscribe((media_list: SearchMedia[]) => {
      // console.log('Search results: %o', media_list);
      if (media_list.length === 0) {
        this.searchResults = [this.noSearchResult];
        return;
      }
      this.searchResults = media_list;
    });
  }
}
