import { NgClass, NgFor } from '@angular/common';
import { Component, ElementRef, HostListener, ViewChild } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Subscription } from 'rxjs';
import { SidenavComponent } from './nav/sidenav/sidenav.component';
import { TopnavComponent } from './nav/topnav/topnav.component';
import { MessageData, WebsocketService } from './services/websocket.service';

@Component({
    selector: 'app-root',
    imports: [RouterOutlet, TopnavComponent, SidenavComponent, NgFor, NgClass],
    templateUrl: './app.component.html',
    styleUrl: './app.component.css'
})
export class AppComponent {
  messages: MessageData[] = [];
  private toastSubscription?: Subscription;

  private timeoutId: any;
  private readonly IDLE_LIMIT: number = 10 * 60 * 1000; // 10 minutes in milliseconds

  constructor(private websocketService: WebsocketService) { }

  ngOnInit() {
    // Reset the idle timer
    this.resetIdleTimer();

    // Subscribe to messages and display them
    this.toastSubscription = this.websocketService.toastMessage.subscribe({
      next: (data: MessageData) => {
        this.messages.unshift(data);
        setTimeout(() => {
          this.messages.pop();
        }, 3000);
      }
    });
  }

  // Uncomment the below code to enable mouse movement detection too!
  // @HostListener('document:mousemove', ['$event']) 
  @HostListener('document:click', ['$event'])
  @HostListener('document:keypress', ['$event'])
  resetIdleTimer(): void {
    // Activity detected, reset the idle timer
    clearTimeout(this.timeoutId);
    this.timeoutId = setTimeout(() => {
      this.closeAllSubscriptions();
    }, this.IDLE_LIMIT);
  }

  closeAllSubscriptions() {
    console.log('Session Idle, closing all subscriptions!');
    // Show Session timed out dialog
    this.showDialog();
    // and show a button to reload the page
    // Close the websocket connection
    this.websocketService.close();
    // Unsubscribe from the websocket and toast messages
    this.toastSubscription?.unsubscribe();
    // Clear api_key from cookies
    document.cookie = 'trailarr_api_key=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  }

  ngOnDestroy() {
    this.closeAllSubscriptions();
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
  }

  // Reference to the dialog element
  @ViewChild('sessionEndedDialog') sessionEndedDialog!: ElementRef<HTMLDialogElement>;

  showDialog(): void {
    this.sessionEndedDialog.nativeElement.showModal();
  }

  reloadPage(): void {
    window.location.reload();
  }
}
