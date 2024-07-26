import { NgClass, NgFor, NgIf } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Component, HostListener } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Subscription } from 'rxjs';
import { SidenavComponent } from './nav/sidenav/sidenav.component';
import { TopnavComponent } from './nav/topnav/topnav.component';
import { MessageData, WebsocketService } from './services/websocket.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, TopnavComponent, SidenavComponent, HttpClientModule, NgIf, NgFor, NgClass],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  messages: MessageData[] = [];
  private toastSubscription?: Subscription;
  private websocketSubscription?: Subscription;

  private idleTime: number = 0;
  private timeoutId: any;
  private readonly IDLE_LIMIT: number = 2 * 60 * 1000; // 2 minutes in milliseconds


  constructor(private websocketService: WebsocketService) { }

  ngOnInit() {
    // Reset the idle timer
    this.resetIdleTimer();
    // Subscribe to the WebSocket events and display the messages
    this.websocketSubscription = this.websocketService.connect().subscribe({
      next: (data: MessageData) => {
        this.messages.unshift(data);
        setTimeout(() => {
          this.messages.pop();
        }, 3000);
      },
      error: (error) => {
        console.error('Error:', error);
      },
      complete: () => {
        console.log('Connection closed');
      }
    })

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
    this.idleTime = 0;
    this.timeoutId = setTimeout(() => {
      this.closeAllSubscriptions();
    }, this.IDLE_LIMIT);
  }

  closeAllSubscriptions() {
    console.log('Session Idle, closing all subscriptions!');
    // TODO: May be display a dialog saying session was idle so closed it
    // and show a button to reload the page
    // Close the websocket connection
    this.websocketService.close();
    // Unsubscribe from the websocket and toast messages
    this.websocketSubscription?.unsubscribe();
    this.toastSubscription?.unsubscribe();
  }

  ngOnDestroy() {
    this.closeAllSubscriptions();
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
  }
}
