import { Location, NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Connection, ConnectionUpdate } from '../../../models/connection';
import { SettingsService } from '../../../services/settings.service';

@Component({
  selector: 'app-edit-connection',
  standalone: true,
  imports: [ReactiveFormsModule, NgFor, NgIf, UpperCasePipe],
  templateUrl: './edit-connection.component.html',
  styleUrl: './edit-connection.component.css'
})
export class EditConnectionComponent {
  constructor(
    private _location: Location,
    private settingsService: SettingsService,
    private route: ActivatedRoute
  ) { }

  connectionId: number = 0;
  ngOnInit() {
    this.route.params.subscribe(params => {
      this.connectionId = params['id'];
      this.settingsService.getConnection(this.connectionId).subscribe((conn: Connection) => {
        this.editConnectionForm.patchValue({
          name: conn.name,
          arrType: conn.arr_type,
          monitorType: conn.monitor,
          url: conn.url,
          apiKey: conn.api_key
        });
      });
    });
  }

  arrOptions = ['radarr', 'sonarr'];
  monitorOptions = ['missing', 'new', 'sync'];
  name = new FormControl('', [Validators.required, Validators.minLength(3)]);
  url = new FormControl('', [Validators.required, Validators.pattern('https?://.*:\\d{2,}')]);
  apiKey = new FormControl('', [Validators.required, Validators.minLength(32), Validators.maxLength(50)]);
  editConnectionForm = new FormGroup({
    name: this.name,
    arrType: new FormControl('radarr'),
    monitorType: new FormControl('new'),
    url: this.url,
    apiKey: this.apiKey
  });

  setArrType(selectedArrType: string) {
    this.editConnectionForm.patchValue({ arrType: selectedArrType });
  }
  setMonitorType(selectedMonitorType: string) {
    this.editConnectionForm.patchValue({ monitorType: selectedMonitorType });
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
    if (this.editConnectionForm.dirty) {
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
    if (this.editConnectionForm.invalid) {
      return;
    }
    const updatedConnection: ConnectionUpdate = {
      id: this.connectionId,
      name: this.editConnectionForm.value.name || '',
      arr_type: this.editConnectionForm.value.arrType || '',
      url: this.editConnectionForm.value.url || '',
      api_key: this.editConnectionForm.value.apiKey || '',
      monitor: this.editConnectionForm.value.monitorType || ''
    };
    this.settingsService.updateConnection(updatedConnection).subscribe((result: string) => {
      this.addConnResult = result;
      //check if result contains version in it
      if (result.toLowerCase().includes("success")) {
        // wait 3 seconds and go back
        setTimeout(() => {
          this._location.back();
        }, 2000);
      }
    });
  }
}
