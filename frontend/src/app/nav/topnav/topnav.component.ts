import {ChangeDetectionStrategy, Component, effect, ElementRef, HostListener, inject, Renderer2, signal} from '@angular/core';
import {debounce, Field, form} from '@angular/forms/signals';
import {Router, RouterLink} from '@angular/router';
import {SettingsService} from 'src/app/services/settings.service';
import {WebsocketService} from 'src/app/services/websocket.service';
import {RouteHome, RouteMedia} from 'src/routing';
import {SearchMedia} from '../../models/media';
import {MediaService} from '../../services/media.service';

@Component({
  selector: 'app-topnav',
  imports: [RouterLink, Field, RouterLink],
  templateUrl: './topnav.component.html',
  styleUrl: './topnav.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TopnavComponent {
  private readonly elementRef = inject(ElementRef);
  private readonly mediaService = inject(MediaService);
  private readonly renderer = inject(Renderer2);
  private readonly router = inject(Router);
  private readonly settingsService = inject(SettingsService);
  private readonly websocketService = inject(WebsocketService);

  searchQuery = signal({
    query: '',
  });
  searchForm = form(this.searchQuery, (schema) => {
    debounce(schema.query, 400);
  });
  previousSearchQuery = signal('');
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
  searchQueryEffect = effect(() => {
    const query = this.searchQuery().query;
    // Ensure we only search when query changes
    if (query === this.previousSearchQuery()) {
      return;
    }
    // Ensure search query is at least 3 characters
    if (query.length < 3) {
      this.searchResults.set([]);
      this.previousSearchQuery.set('');
      return;
    }
    // Perform search
    this.previousSearchQuery.set(query);
    this.onSearch(query);
  });

  clearSearchResults() {
    this.searchResults.set([]);
    this.searchQuery.set({query: ''});
    this.searchForm().reset();
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
        event.preventDefault();
        // const selectedResult = this.searchResults[this.selectedIndex];
        this.router.navigate([RouteMedia, this.selectedId()]);
        this.clearSearchResults();
        return;
      }
    }
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

  protected readonly noSearchResult: SearchMedia = {
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
    // console.log('Search query: %s', this.searchQuery);
    this.mediaService.searchMedia(query).subscribe((media_list: SearchMedia[]) => {
      // console.log('Search results: %o', media_list);
      if (media_list.length === 0) {
        this.searchResults.set([this.noSearchResult]);
        return;
      }
      this.searchResults.set(media_list);
    });
  }
}
