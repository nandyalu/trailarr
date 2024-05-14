import { DatePipe, Location, NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Connection } from '../../../models/connection';
import { SettingsService } from '../../settings.service';

@Component({
  selector: 'app-show-connections',
  standalone: true,
  imports: [DatePipe, NgIf, NgFor, RouterLink, UpperCasePipe],
  templateUrl: './show-connections.component.html',
  styleUrl: './show-connections.component.css'
})
export class ShowConnectionsComponent {
  connectionList: Connection[] = [];
  isLoading = false;
  resultMessage = '';
  resultType = '';

  constructor(private _location: Location, private settingsService: SettingsService) { }

  ngOnInit() {
    this.getConnections();
  }
    
  getConnections() {
    this.isLoading = true;
    this.settingsService.getConnections().subscribe((connections: Connection[]) => {
      this.connectionList = connections;
      this.isLoading = false;
    });
  }

  showDialog = false;
  selectedId = 0;
  onConfirmDelete() {
    this.showDialog = false;
    this.settingsService.deleteConnection(this.selectedId).subscribe((res: string) => {
      this.resultType = 'error';
      if (res.toLowerCase().includes('success')) {
        this.resultType = 'success';
      }
      this.resultMessage = res;
      this.getConnections();
      setTimeout(() => {
          this.resultMessage = '';
        }, 3000);
    })
  }
}
