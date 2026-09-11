import {httpResource} from '@angular/common/http';
import {ChangeDetectionStrategy, Component, computed, effect, inject, signal, untracked} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import {catchError, of} from 'rxjs';
import {environment} from '../../environment';
import {mapPendingSummary, PendingSummary, PendingSummaryItem} from '../models/pending';
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

  /** How many media items the first sync has read. */
  readonly mediaCount = computed(() => this.setupService.status()?.media ?? 0);

  /** True while that number goes up. Step 4 says so, because a library of
   * 10,000 items takes minutes and a count that never moves looks stuck. */
  readonly stillReading = signal(false);
  private countAtLastPoll = -1;

  /** How many rows step 4 reads at a time, and how far it has read. A
   * first sync of 10,000 items must not arrive in one response (C4). */
  readonly pageSize = 25;
  readonly previewOffset = signal(0);

  /** Every row read so far. Each page is added as it arrives. */
  readonly shownItems = signal<PendingSummaryItem[]>([]);

  /** What the first run would download. Read only while the guide is on
   * step 4, so opening the guide does not scan the library. The counts
   * above the list are the library totals, not the page. */
  readonly previewResource = httpResource<PendingSummary | null>(
    () =>
      this.step() === 4
        ? {
            url: environment.apiUrl + environment.media + 'pending',
            params: {limit: this.pageSize, offset: this.previewOffset()},
          }
        : undefined,
    {
      defaultValue: null,
      parse: (response) => (response ? mapPendingSummary(response) : null),
    },
  );

  readonly preview = computed(() => this.previewResource.value());
  readonly previewLoading = computed(() => this.previewResource.isLoading());

  /** Adds each page to the list on screen. The response says which offset
   * it answers, so a reload cannot put the same rows in twice. */
  private appendedOffset = -1;
  private readonly collectPages = effect(() => {
    const page = this.previewResource.value();
    if (!page || page.offset === this.appendedOffset) {
      return;
    }
    this.appendedOffset = page.offset;
    this.shownItems.update((items) => (page.offset === 0 ? page.items : [...items, ...page.items]));
  });

  /** One row is one (media item, profile) pair, the same as the list. */
  readonly totalPairs = computed(() => {
    const summary = this.preview();
    return summary ? summary.pending_pairs + summary.backoff_pairs : 0;
  });
  readonly remainingCount = computed(() => Math.max(0, this.totalPairs() - this.shownItems().length));
  readonly hasMoreToShow = computed(() => this.remainingCount() > 0);

  /** Step 4 asks the server again every few seconds while it is on screen.
   * A first sync is the one time the numbers change under the user. */
  private readonly pollFirstSync = effect((onCleanup) => {
    if (this.step() !== 4) {
      return;
    }
    // The count the step opened with. The first poll after it compares
    // against this, so a sync that is already running shows as running.
    this.countAtLastPoll = untracked(() => this.mediaCount());
    const handle = setInterval(() => this.pollStatus(), 4000);
    onCleanup(() => clearInterval(handle));
  });

  private pollStatus() {
    this.setupService.loadStatus().subscribe((status) => {
      const grew = status.media > this.countAtLastPoll;
      this.stillReading.set(grew);
      this.countAtLastPoll = status.media;
      // The first items to arrive are worth showing without a click.
      if (grew && this.shownItems().length === 0) {
        this.reloadPreview();
      }
    });
  }

  /** Reads the next page of the list. */
  showMore() {
    this.previewOffset.update((offset) => offset + this.pageSize);
  }

  /** Reads the list again from the start. */
  private reloadPreview() {
    this.appendedOffset = -1;
    this.shownItems.set([]);
    if (this.previewOffset() === 0) {
      this.previewResource.reload();
    } else {
      this.previewOffset.set(0);
    }
  }

  /** Re-reads the counts that steps 2 and 4 show. */
  refreshCounts() {
    this.connectionService.connectionsResource.reload();
    this.setupService.loadStatus().subscribe((status) => {
      this.countAtLastPoll = status.media;
    });
    this.reloadPreview();
  }

  private readStep(): number {
    const stored = Number(localStorage.getItem('TrailarrSetupStep') ?? '1');
    return stored >= 1 && stored <= 5 ? stored : 1;
  }

  goTo(step: number) {
    const next = Math.min(Math.max(step, 1), this.totalSteps);
    if (next === 4 && this.step() !== 4) {
      this.appendedOffset = -1;
      this.shownItems.set([]);
      this.previewOffset.set(0);
    }
    this.step.set(next);
    localStorage.setItem('TrailarrSetupStep', String(next));
  }

  next() {
    this.goTo(this.step() + 1);
  }

  back() {
    this.goTo(this.step() - 1);
  }

  /** Leaves step 4 while the first sync continues. The sync is a task on
   * the server — it does not stop when the guide moves on. */
  continueInBackground() {
    this.goTo(5);
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
