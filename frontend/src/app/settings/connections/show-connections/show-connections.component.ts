import {DatePipe, Location, NgFor, NgIf, UpperCasePipe} from '@angular/common';
import {Component, ElementRef, inject, OnInit, ViewChild} from '@angular/core';
import {RouterLink} from '@angular/router';
import {RouteAdd, RouteConnections, RouteEdit, RouteSettings} from 'src/routing';
import {Connection} from '../../../models/connection';
import {SettingsService} from '../../../services/settings.service';

@Component({
  selector: 'app-show-connections',
  imports: [DatePipe, NgIf, NgFor, RouterLink, UpperCasePipe],
  templateUrl: './show-connections.component.html',
  styleUrl: './show-connections.component.scss',
})
export class ShowConnectionsComponent implements OnInit {
  private readonly _location = inject(Location);
  private readonly settingsService = inject(SettingsService);

  connectionList: Connection[] = [];
  isLoading = false;
  resultMessage = '';
  resultType = '';

  protected readonly RouteAdd = RouteAdd;
  protected readonly RouteConnections = RouteConnections;
  protected readonly RouteEdit = RouteEdit;
  protected readonly RouteSettings = RouteSettings;

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

  // Reference to the dialog element
  @ViewChild('deleteConnectionDialog') deleteConnectionDialog!: ElementRef<HTMLDialogElement>;

  showDeleteDialog(): void {
    this.deleteConnectionDialog.nativeElement.showModal(); // Open the dialog
  }

  closeDeleteDialog(): void {
    this.deleteConnectionDialog.nativeElement.close(); // Close the dialog
  }

  // showDialog = false;
  selectedId = 0;
  onConfirmDelete() {
    // this.showDialog = false;
    this.closeDeleteDialog();
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
    });
  }
}
