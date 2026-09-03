import {AsyncPipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, effect, ElementRef, inject, OnDestroy, OnInit, signal, viewChild} from '@angular/core';
import {Router, RouterOutlet} from '@angular/router';
import {msMinute} from 'src/util';
import {TimeRemainingPipe} from './shared/pipes/time-remaining.pipe';
import {SidenavComponent} from './nav/sidenav/sidenav.component';
import {TopnavComponent} from './nav/topnav/topnav.component';
import {NotificationsComponent} from './notifications/notifications.component';
import {AuthService} from './services/auth.service';
import {SettingsService} from './services/settings.service';
import {WebsocketService} from './services/websocket.service';
import {LoadIndicatorComponent} from './shared/load-indicator';

@Component({
  selector: 'app-root',
  imports: [AsyncPipe, LoadIndicatorComponent, NotificationsComponent, RouterOutlet, TimeRemainingPipe, TopnavComponent, SidenavComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '(document:click)': 'resetIdleTimer()',
    '(document:keypress)': 'resetIdleTimer()',
  },
})
export class AppComponent implements OnDestroy, OnInit {
  protected readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly settingsService = inject(SettingsService);
  private readonly websocketService = inject(WebsocketService);

  /** With auth disabled there is no session to end — a logout would only
   * bounce through /login and come back with a fresh session. The idle
   * flow pauses live updates instead (see sessionPaused). */
  protected readonly authDisabled = computed(() => this.settingsService.settings()?.webui_disable_auth ?? false);
  /** True after the idle countdown ran out with auth disabled: the
   * websocket is closed and the dialog stays open until the user resumes. */
  protected readonly sessionPaused = signal(false);

  constructor() {
    effect(() => {
      if (this.authService.isAuthenticated()) {
        this.websocketService.connect();
      }
    });
  }

  private extendTimeoutId: any;
  private sessionTimeoutId: any;
  private readonly IDLE_LIMIT: number = 12 * msMinute;
  private readonly EXTEND_LIMIT: number = 3 * msMinute;
  protected sessionEndTime = signal<number>(Date.now() + this.IDLE_LIMIT + this.EXTEND_LIMIT);

  ngOnInit() {
    this.resetIdleTimer();
  }

  // Uncomment the below code to enable mouse movement detection too!
  // host: { '(document:mousemove)': 'resetIdleTimer()' }
  resetIdleTimer(): void {
    // While paused, only an explicit Resume (or Esc) restarts the timers
    if (this.sessionPaused()) return;
    // Activity detected, reset the idle timer
    clearTimeout(this.sessionTimeoutId);
    clearTimeout(this.extendTimeoutId);
    // Reset the time remaining signal
    this.extendTimeoutId = setTimeout(() => {
      // Update the time remaining signal
      this.showEndingDialog();
    }, this.IDLE_LIMIT);
  }

  closeAllSubscriptions() {
    this.websocketService.close();
    if (this.authDisabled()) {
      // Delete the session server-side so the old session id gets 401s,
      // but keep the app shell mounted (no isAuthenticated flip, no
      // /login round-trip — it would only mint a new session).
      this.authService.endSession().subscribe();
      return;
    }
    this.authService.logout().subscribe(() => {
      this.router.navigate(['/login']);
    });
  }

  ngOnDestroy() {
    this.closeAllSubscriptions();
    if (this.extendTimeoutId) {
      clearTimeout(this.extendTimeoutId);
    }
    if (this.sessionTimeoutId) {
      clearTimeout(this.sessionTimeoutId);
    }
  }

  // Non-required: dialogs are only in the DOM when isAuthenticated() is true
  readonly sessionEndingDialog = viewChild<ElementRef<HTMLDialogElement>>('sessionEndingDialog');

  showEndingDialog(): void {
    this.sessionEndTime.set(Date.now() + this.EXTEND_LIMIT);
    this.sessionEndingDialog()?.nativeElement.showModal();
    this.sessionTimeoutId = setTimeout(() => {
      if (this.authDisabled()) {
        this.pauseSession();
      } else {
        this.closeAllSubscriptions();
      }
    }, this.EXTEND_LIMIT);
  }

  closeEndingDialog(): void {
    this.sessionEndingDialog()?.nativeElement.close();
  }

  extendTime(): void {
    this.sessionEndTime.set(Date.now() + this.EXTEND_LIMIT);
    this.resetIdleTimer();
    this.closeEndingDialog();
  }

  /** Idle countdown ran out with auth disabled: stop live updates,
   * delete the session server-side (so the old session id gets 401s),
   * and keep the dialog open in its paused state. */
  pauseSession(): void {
    this.closeAllSubscriptions();
    this.sessionPaused.set(true);
  }

  /** The user is back: get a fresh session first (the paused one was
   * deleted), then reconnect live updates and restart the idle timer. */
  resumeSession(): void {
    this.authService.checkAuthStatus().subscribe((ok) => {
      if (!ok) return; // server unreachable — stay paused
      this.sessionPaused.set(false);
      this.websocketService.connect();
      this.closeEndingDialog();
      this.resetIdleTimer();
    });
  }

  /** Esc on the dialog: while paused it means "I am back" — resume
   * instead of leaving the app without live updates and no dialog. */
  onDialogCancel(event: Event): void {
    if (this.sessionPaused()) {
      event.preventDefault();
      this.resumeSession();
    }
  }
}
