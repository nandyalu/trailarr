import {Injectable} from '@angular/core';
import {Observable, Subject, Subscription} from 'rxjs';
import {webSocket, WebSocketSubject} from 'rxjs/webSocket';

export interface MessageData {
  message: string;
  type: string;
}

@Injectable({
  providedIn: 'root',
})
export class WebsocketService {
  private socket$!: WebSocketSubject<any>;
  websocketSubscription?: Subscription;
  toastMessage = new Subject<MessageData>();

  constructor() {
    this.connect();
  }

  public connect(): Observable<MessageData> {
    if (!this.socket$ || this.socket$.closed) {
      const client_id = Math.floor(Math.random() * 1000000);
      // this.socket$ = webSocket('ws://10.0.10.131:7889/ws/' + client_id);
      // Determine the WebSocket protocol based on the current page protocol
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // Use the current hostname
      const hostname = window.location.hostname;
      // Use the port if needed, or leave it empty for default ports (80 for ws and 443 for wss)
      const port = window.location.port ? `:${window.location.port}` : ''; // Use the current port or specify one
      // Construct the WebSocket URL dynamically
      const wsUrl = `${wsProtocol}//${hostname}${port}/ws/${client_id}`;

      this.socket$ = webSocket(wsUrl);

      // Subscribe to the WebSocket and handle incoming messages
      this.websocketSubscription = this.socket$.subscribe({
        next: (data: MessageData) => {
          this.toastMessage.next(data);
        },
        error: (error) => {
          console.error('WebSocket error:', error);
        },
        complete: () => {
          console.log('WebSocket connection closed');
        },
      });
    }
    return this.socket$.asObservable();
  }

  public showToast(message: string, type: string = 'Success'): void {
    this.toastMessage.next({message, type});
  }

  close() {
    if (this.websocketSubscription) {
      this.websocketSubscription.unsubscribe();
    }
    this.socket$.complete();
  }
}
