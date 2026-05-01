import {AsyncPipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, ElementRef, HostListener, inject, OnDestroy, OnInit, signal, viewChild} from '@angular/core';
import {Router, RouterOutlet} from '@angular/router';
import {Subscription} from 'rxjs';
import {msMinute} from 'src/util';
import {TimeRemainingPipe} from './helpers/time-remaining.pipe';
import {SidenavComponent} from './nav/sidenav/sidenav.component';
import {TopnavComponent} from './nav/topnav/topnav.component';
import {AuthService} from './services/auth.service';
import {MessageData, WebsocketService} from './services/websocket.service';
import {LoadIndicatorComponent} from './shared/load-indicator';

@Component({
  selector: 'app-root',
  imports: [AsyncPipe, LoadIndicatorComponent, RouterOutlet, TimeRemainingPipe, TopnavComponent, SidenavComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent implements OnDestroy, OnInit {
  protected readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly websocketService = inject(WebsocketService);

  protected messages = signal<MessageData[]>([]);
  private toastSubscription?: Subscription;

  private extendTimeoutId: any;
  private sessionTimeoutId: any;
  private readonly IDLE_LIMIT: number = 12 * msMinute;
  private readonly EXTEND_LIMIT: number = 3 * msMinute;
  protected sessionEndTime = signal<number>(Date.now() + this.IDLE_LIMIT + this.EXTEND_LIMIT);

  ngOnInit() {
    // Reset the idle timer
    this.resetIdleTimer();

    // Subscribe to messages and display them
    this.toastSubscription = this.websocketService.toastMessage.subscribe({
      next: (data: MessageData) => {
        this.messages.update((msgs) => [...msgs, data]);
        setTimeout(() => {
          // Remove last message after 3 seconds
          this.messages.update((msgs) => msgs.filter((msg) => msg !== data));
        }, 3000);
      },
    });
  }

  // Uncomment the below code to enable mouse movement detection too!
  // @HostListener('document:mousemove', ['$event'])
  @HostListener('document:click')
  @HostListener('document:keypress')
  resetIdleTimer(): void {
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
    this.showEndedDialog();
    this.websocketService.close();
    this.toastSubscription?.unsubscribe();
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
  readonly sessionEndedDialog = viewChild<ElementRef<HTMLDialogElement>>('sessionEndedDialog');

  showEndingDialog(): void {
    this.sessionEndTime.set(Date.now() + this.EXTEND_LIMIT);
    this.sessionEndingDialog()?.nativeElement.showModal();
    this.sessionTimeoutId = setTimeout(() => {
      this.closeAllSubscriptions();
    }, this.EXTEND_LIMIT);
  }

  showEndedDialog(): void {
    this.closeEndingDialog();
    this.sessionEndedDialog()?.nativeElement.showModal();
  }

  closeEndingDialog(): void {
    this.sessionEndingDialog()?.nativeElement.close();
  }

  extendTime(): void {
    this.sessionEndTime.set(Date.now() + this.EXTEND_LIMIT);
    this.resetIdleTimer();
    this.closeEndingDialog();
  }

  reloadPage(): void {
    this.router.navigate(['/login']);
  }
}
