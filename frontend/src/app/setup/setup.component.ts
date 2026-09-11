import {httpResource} from '@angular/common/http';
import {ChangeDetectionStrategy, Component, computed, inject, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import {catchError, of} from 'rxjs';
import {environment} from '../../environment';
import {mapPendingSummary, PendingSummary} from '../models/pending';
import {ConnectionService} from '../services/connection.service';
import {SettingsService} from '../services/settings.service';
import {SetupService} from '../services/setup.service';
import {WebsocketService} from '../services/websocket.service';
import {RouteConnections, RouteSettings} from 'src/routing';

/**
 * The first-run setup guide.
 *
 * Five steps, in the order a new install needs them: what Trailarr does,
 * a connection, the optional TMDB key, what the first run would download,
 * and then turning downloads on.
 *
 * Two rules run through it. Nothing here is a dead end — every step can be
 * skipped, because a setup screen that argues with someone in a hurry is
 * worse than no screen. And nothing here is special state: a connection
 * added in step 2 is just a connection, so leaving halfway leaves a
 * working installation behind (wargame C3).
 */
@Component({
  selector: 'app-setup',
  imports: [FormsModule, RouterLink],
  templateUrl: './setup.component.html',
  styleUrl: './setup.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SetupComponent {
  private readonly setupService = inject(SetupService);
  private readonly connectionService = inject(ConnectionService);
  private readonly settingsService = inject(SettingsService);
  private readonly webSocketService = inject(WebsocketService);
  private readonly router = inject(Router);

  protected readonly RouteSettings = RouteSettings;
  protected readonly RouteConnections = RouteConnections;

  /** Which step is on screen, 1 to 5. Kept so that going to the
   * connections page and back does not restart the guide (wargame C3). */
  readonly step = signal(this.readStep());

  readonly totalSteps = 5;
  readonly tmdbKey = signal('');
  readonly savingKey = signal(false);
  readonly keyMessage = signal('');

  /** Connections the user has added. Step 2 watches this. */
  readonly connections = computed(() => this.connectionService.connectionsResource.value() ?? []);
  readonly hasConnection = computed(() => this.connections().length > 0);

  readonly settings = computed(() => this.settingsService.settings());
  readonly hasTmdbKey = computed(() => !!this.settings()?.tmdb_api_key);

  /** What the first run would download. Read only while the guide is on
   * step 4, so opening the guide does not scan the library. The limit
   * keeps a first sync of 10,000 items from sending everything at once
   * (wargame C4); the count above the list is the real total. */
  readonly previewResource = httpResource<PendingSummary | null>(
    () =>
      this.step() === 4
        ? {url: environment.apiUrl + environment.media + 'pending', params: {limit: 100}}
        : undefined,
    {
      defaultValue: null,
      parse: (response) => (response ? mapPendingSummary(response) : null),
    },
  );
  readonly preview = computed(() => this.previewResource.value());
  readonly previewLoading = computed(() => this.previewResource.isLoading());

  /** How many media items the first sync has brought in so far. */
  readonly mediaCount = computed(() => this.setupService.status()?.media ?? 0);

  /** Re-reads the counts that steps 2 and 4 show. */
  refreshCounts() {
    this.connectionService.connectionsResource.reload();
    this.setupService.loadStatus().subscribe();
    this.previewResource.reload();
  }

  private readStep(): number {
    const stored = Number(localStorage.getItem('TrailarrSetupStep') ?? '1');
    return stored >= 1 && stored <= 5 ? stored : 1;
  }

  goTo(step: number) {
    const next = Math.min(Math.max(step, 1), this.totalSteps);
    this.step.set(next);
    localStorage.setItem('TrailarrSetupStep', String(next));
  }

  next() {
    this.goTo(this.step() + 1);
  }

  back() {
    this.goTo(this.step() - 1);
  }

  /** Saves the TMDB key from step 3. The server checks it first. */
  saveTmdbKey() {
    const key = this.tmdbKey().trim();
    if (!key) {
      this.next();
      return;
    }
    this.savingKey.set(true);
    this.keyMessage.set('');
    this.settingsService
      .updateSetting('tmdb_api_key', key)
      .pipe(
        catchError(() => {
          this.keyMessage.set('Trailarr could not save the key. You can add it later in Settings.');
          this.savingKey.set(false);
          return of(null);
        }),
      )
      .subscribe((message) => {
        this.savingKey.set(false);
        if (message === null) {
          return;
        }
        const text = String(message);
        if (text.startsWith('Error')) {
          this.keyMessage.set(text.replace('Error updating setting: ', ''));
          return;
        }
        this.tmdbKey.set('');
        this.settingsService.settingsResource.reload();
        this.next();
      });
  }

  /** Turns downloads on and leaves the guide. */
  finish(enableDownloads: boolean) {
    if (enableDownloads) {
      this.settingsService.updateSetting('downloads_enabled', true).subscribe();
    }
    this.leave();
  }

  /** Records the guide as done and goes to the library. */
  leave() {
    this.setupService
      .complete()
      .pipe(catchError(() => of(null)))
      .subscribe(() => {
        localStorage.removeItem('TrailarrSetupStep');
        this.webSocketService.showToast('Setup complete. Welcome to Trailarr!');
        this.router.navigate(['/']);
      });
  }
}
