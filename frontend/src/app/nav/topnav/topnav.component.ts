import {Component, DestroyRef, effect, ElementRef, HostListener, inject, OnInit, Renderer2, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import {debounceTime, distinctUntilChanged} from 'rxjs/operators';
import {SettingsService} from 'src/app/services/settings.service';
import {WebsocketService} from 'src/app/services/websocket.service';
import {RouteHome, RouteMedia} from 'src/routing';
import {SearchMedia} from '../../models/media';
import {MediaService} from '../../services/media.service';

@Component({
  selector: 'app-topnav',
  imports: [RouterLink, FormsModule, ReactiveFormsModule, RouterLink],
  templateUrl: './topnav.component.html',
  styleUrl: './topnav.component.scss',
})
export class TopnavComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  private readonly elementRef = inject(ElementRef);
  private readonly mediaService = inject(MediaService);
  private readonly renderer = inject(Renderer2);
  private readonly router = inject(Router);
  private readonly settingsService = inject(SettingsService);
  private readonly websocketService = inject(WebsocketService);

  isDarkModeEnabled = true;
  searchQuery = signal('');
  searchForm = new FormControl();
  searchResults = signal<SearchMedia[]>([]);
  selectedIndex = signal(-1);
  selectedId = signal(-1);

  protected readonly RouteHome = RouteHome;

  // Get theme from settings and apply it
  setThemeEffect = effect(() => {
    let theme = this.settingsService.settingsResource.value()?.app_theme || 'auto';
    theme = theme.toLowerCase().trim();
    if (theme === 'auto') {
      const darkTheme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      theme = darkTheme ? 'dark' : 'light';
    }
    this.renderer.setAttribute(document.documentElement, 'theme', theme);
    this.renderer.removeClass(document.body, 'light');
    this.renderer.removeClass(document.body, 'dark');
    this.renderer.addClass(document.body, theme);
    // console.log('Theme set to %s', theme);
    // return;
  });

  clearSearchResults() {
    this.searchResults.set([]);
    this.searchQuery.set('');
    this.searchForm.reset();
    this.selectedId.set(-1);
    this.selectedIndex.set(-1);
  }

  @HostListener('document:click', ['$event'])
  clickout(event: Event) {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.clearSearchResults();
    }
  }

  @HostListener('document:mousemove', ['$event'])
  disableSelection(event: Event) {
    if (this.searchResults().length > 0) {
      this.selectedId.set(-1);
      this.selectedIndex.set(-1);
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
    if (this.searchResults().length > 0) {
      if (event.key === 'Escape') {
        this.clearSearchResults();
        return;
      }
      let firstId = this.searchResults()[0].id;
      let lastId = this.searchResults()[this.searchResults().length - 1].id;
      if (event.key === 'ArrowDown' || (event.key === 'Tab' && !event.shiftKey)) {
        event.preventDefault();
        // If the last item is selected, loop back to the first item
        if (this.selectedId() === lastId) {
          this.selectedIndex.set(0);
          this.selectedId.set(firstId);
          return;
        }
        // Else, select the next item
        this.selectedIndex.update((value) => value + 1);
        this.selectedId.set(this.searchResults()[this.selectedIndex()].id);
        return;
      } else if (event.key === 'ArrowUp' || (event.shiftKey && event.key === 'Tab')) {
        event.preventDefault();
        // If the first item is selected, loop back to the last item
        if (this.selectedId() === firstId) {
          this.selectedIndex.set(this.searchResults().length - 1);
          this.selectedId.set(lastId);
          return;
        }
        // Else, select the previous item
        this.selectedIndex.update((value) => value - 1);
        this.selectedId.set(this.searchResults()[this.selectedIndex()].id);
        return;
      } else if (event.key === 'Enter' && this.selectedId() !== -1) {
        // const selectedResult = this.searchResults[this.selectedIndex];
        this.router.navigate([RouteMedia, this.selectedId()]);
        this.clearSearchResults();
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
  }

  logout() {
    // Clear api_key from cookies first
    document.cookie = 'trailarr_api_key=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; secure;';

    console.log('Logging out...');

    // Close all subscriptions to WebSocket to avoid memory leaks
    this.websocketService.close();

    // Call logout endpoint to clear browser's Basic Auth credentials
    // This will cause a 401 response which clears the browser's cached credentials
    this.settingsService.logout().subscribe({
      next: () => {
        // This won't execute since logout always returns 401
        console.log('Logout successful, reloading page...');
        window.location.reload();
      },
      error: () => {
        // The 401 response is expected - it clears the cached credentials
        console.log('Browser credentials cleared, reloading page...');
        // Force page reload to show login dialog
        window.location.reload();
      },
    });
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
      this.searchResults.set([]);
      return;
    }
    if (query.trim() === this.searchQuery()) {
      return;
    }
    this.searchQuery.set(query);
    // console.log('Search query: %s', this.searchQuery);
    this.mediaService.searchMedia(this.searchQuery()).subscribe((media_list: SearchMedia[]) => {
      // console.log('Search results: %o', media_list);
      if (media_list.length === 0) {
        this.searchResults.set([this.noSearchResult]);
        return;
      }
      this.searchResults.set(media_list);
    });
  }
}
