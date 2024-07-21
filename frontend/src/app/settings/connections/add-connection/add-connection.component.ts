import { Location, NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ConnectionCreate } from '../../../models/connection';
import { SettingsService } from '../../../services/settings.service';

@Component({
  selector: 'app-add-connection',
  standalone: true,
  imports: [ReactiveFormsModule, NgFor, NgIf, UpperCasePipe],
  templateUrl: './add-connection.component.html',
  styleUrl: './add-connection.component.css'
})
export class AddConnectionComponent {

  constructor(private _location: Location, private settingsService: SettingsService) {}
  arrOptions = ['radarr', 'sonarr'];
  monitorOptions = ['missing', 'new', 'sync'];
  name = new FormControl('', [Validators.required, Validators.minLength(3)]);
  url = new FormControl('', [Validators.required, Validators.pattern('https?://.*:\\d{2,}')]);
  apiKey = new FormControl('', [Validators.required, Validators.minLength(32), Validators.maxLength(50)]);
  addConnectionForm = new FormGroup({
    name: this.name,
    arrType: new FormControl('radarr'),
    monitorType: new FormControl('new'),
    url: this.url,
    apiKey: this.apiKey
  });

  setArrType(selectedArrType: string) {
    this.addConnectionForm.patchValue({ arrType: selectedArrType });
  }
  setMonitorType(selectedMonitorType: string) {
    this.addConnectionForm.patchValue({ monitorType: selectedMonitorType });
  }

  // Reference to the dialog element
  @ViewChild('cancelDialog') cancelDialog!: ElementRef<HTMLDialogElement>;

  showCancelDialog(): void {
    // Open the confirmation dialog
    this.cancelDialog.nativeElement.showModal(); // Open the dialog
  }

  closeCancelDialog(): void {
    // Close the confirmation dialog
    this.cancelDialog.nativeElement.close(); // Close the dialog
  }
  
  onCancel() {
    // Check if form is dirty before showing the dialog, if not go back
    if (this.addConnectionForm.dirty) {
      this.showCancelDialog();
    }
    else {
      this._location.back();
    }
  }

  onConfirmCancel() {
    // Close the dialog and go back
    this.showCancelDialog();
    this._location.back();
  }

  addConnResult: string = '';
  onSubmit() {
    // Check if form is invalid, else submit the form
    if (this.addConnectionForm.invalid) {
      return;
    }
    const newConnection: ConnectionCreate = {
      name: this.addConnectionForm.value.name || '',
      arr_type: this.addConnectionForm.value.arrType || '',
      url: this.addConnectionForm.value.url || '',
      api_key: this.addConnectionForm.value.apiKey || '',
      monitor: this.addConnectionForm.value.monitorType || ''
    };
    this.settingsService.addConnection(newConnection).subscribe((result: string) => {
      this.addConnResult = result;
      //check if result contains version in it
      if (result.toLowerCase().includes("version")) {
        // wait 3 seconds and go back
        setTimeout(() => {
          this._location.back();
        }, 3000);
      }
    });
  }



}
