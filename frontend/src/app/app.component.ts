import { NgClass, NgFor, NgIf } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
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
  title = 'Trailarr';
  messages: MessageData[] = [];

  constructor(private websocketService: WebsocketService) { }

  ngOnInit() {
    // Subscribe to the WebSocket events and display the messages
    this.websocketService.connect().subscribe({
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
  }

  ngOnDestroy() {
    // Close the websocket connection
    this.websocketService.close();
  }

  displayMessage(msg: String) {
    console.log('Message:', msg);
  }
}
