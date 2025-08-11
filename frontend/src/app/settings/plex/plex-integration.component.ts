import {Component, inject, signal, computed, OnDestroy} from '@angular/core';
import {CommonModule} from '@angular/common';
import {
  PlexService,
  AuthStartRequest,
  AuthPollResponse,
  ScanRequest,
  ExtrasRequest
} from '../../services/plex.service';
import {interval, Subscription, switchMap, takeWhile} from 'rxjs';

type PlexAuthState = 'initial' | 'pending' | 'success' | 'error';

@Component({
  selector: 'app-plex-integration',
  imports: [CommonModule],
  templateUrl: './plex-integration.component.html',
  styleUrls: ['./plex-integration.component.scss'],
  standalone: true,
})
export class PlexIntegrationComponent implements OnDestroy {
  private readonly plexService = inject(PlexService);
  private pollingSubscription?: Subscription;

  // State management
  readonly authState = signal<PlexAuthState>('initial');
  readonly pin = signal<string>('');
  readonly authUrl = signal<string>('');
  readonly errorMessage = signal<string>('');
  readonly token = signal<string>('');
  readonly serverAddress = signal<string>('');

  // Computed properties for UI states
  readonly isInitial = computed(() => this.authState() === 'initial');
  readonly isPending = computed(() => this.authState() === 'pending');
  readonly isSuccess = computed(() => this.authState() === 'success');
  readonly isError = computed(() => this.authState() === 'error');

  ngOnDestroy() {
    this.stopPolling();
  }

  /**
   * Start the Plex authentication flow
   */
  connectPlex() {
    this.authState.set('pending');
    this.errorMessage.set('');

    const request: AuthStartRequest = {
      client_identifier: 'trailarr-' + Date.now(),
      product_name: 'Trailarr'
    };

    this.plexService.startAuth(request).subscribe({
      next: (response) => {
        this.pin.set(response.pin);
        this.authUrl.set(response.auth_url);
        
        // Open auth URL in new window
        window.open(response.auth_url, '_blank');
        
        // Start polling for token
        this.startPolling(response.pin);
      },
      error: (error) => {
        console.error('Failed to start Plex auth:', error);
        this.authState.set('error');
        this.errorMessage.set(error.error?.detail || 'Failed to start Plex authentication');
      }
    });
  }

  /**
   * Start polling for authentication token
   */
  private startPolling(pin: string) {
    // Poll every 2 seconds
    this.pollingSubscription = interval(2000)
      .pipe(
        switchMap(() => this.plexService.pollForToken(pin)),
        takeWhile((response: AuthPollResponse) => response.status === 'pending', true)
      )
      .subscribe({
        next: (response) => {
          if (response.status === 'success') {
            this.authState.set('success');
            this.token.set(response.token || '');
            this.serverAddress.set(response.plex_server_address || '');
            this.stopPolling();
          } else if (response.status === 'expired') {
            this.authState.set('error');
            this.errorMessage.set('Authentication PIN has expired. Please try again.');
            this.stopPolling();
          }
          // For 'pending', we continue polling
        },
        error: (error) => {
          console.error('Failed to poll for token:', error);
          this.authState.set('error');
          this.errorMessage.set(error.error?.detail || 'Failed to check authentication status');
          this.stopPolling();
        }
      });
  }

  /**
   * Stop the polling subscription
   */
  private stopPolling() {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
      this.pollingSubscription = undefined;
    }
  }

  /**
   * Disconnect from Plex (reset state)
   */
  disconnectPlex() {
    this.stopPolling();
    this.authState.set('initial');
    this.pin.set('');
    this.authUrl.set('');
    this.token.set('');
    this.serverAddress.set('');
    this.errorMessage.set('');
  }

  /**
   * Try again after an error
   */
  tryAgain() {
    this.authState.set('initial');
    this.errorMessage.set('');
  }

  /**
   * Test functionality - trigger a scan
   */
  testScan() {
    if (!this.token() || !this.serverAddress()) {
      console.error('No token or server address available');
      return;
    }

    const request: ScanRequest = {
      token: this.token(),
      server_address: this.serverAddress(),
      media_folder_path: '/library/movies' // Example path
    };

    this.plexService.triggerScan(request).subscribe({
      next: (response) => {
        console.log('Scan result:', response);
        alert(`Scan triggered: ${response.message}`);
      },
      error: (error) => {
        console.error('Scan failed:', error);
        alert(`Scan failed: ${error.error?.detail || 'Unknown error'}`);
      }
    });
  }

  /**
   * Test functionality - check for extras
   */
  testExtras() {
    if (!this.token() || !this.serverAddress()) {
      console.error('No token or server address available');
      return;
    }

    const request: ExtrasRequest = {
      token: this.token(),
      server_address: this.serverAddress(),
      media_type: 'movie',
      tmdb_id: '550' // Fight Club as example
    };

    this.plexService.checkExtras(request).subscribe({
      next: (response) => {
        console.log('Extras result:', response);
        const message = response.has_extras 
          ? `Found ${response.extras.length} extras: ${response.extras.map(e => e.title).join(', ')}`
          : 'No extras found';
        alert(message);
      },
      error: (error) => {
        console.error('Extras check failed:', error);
        alert(`Extras check failed: ${error.error?.detail || 'Unknown error'}`);
      }
    });
  }
}