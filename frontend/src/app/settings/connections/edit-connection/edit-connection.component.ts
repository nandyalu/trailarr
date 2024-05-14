import { Location, NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { Component } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Connection, ConnectionUpdate } from '../../../models/connection';
import { SettingsService } from '../../settings.service';

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
  showDialog = false;
  onCancel() {
    if (this.editConnectionForm.dirty) {
      this.showDialog = true;
    }
    else {
      this._location.back();
    }
  }
  onConfirmCancel() {
    this.showDialog = false;
    this._location.back();
  }
  onCancelDialog() {
    this.showDialog = false;
  }

  addConnResult: string = '';
  onSubmit() {
    console.log('ID: ', this.connectionId);
    console.log('Name: ', this.editConnectionForm.value.name);
    console.log('Selected Arr:', this.editConnectionForm.value.arrType);
    console.log('Selected Monitor:', this.editConnectionForm.value.monitorType);
    console.log('URL: ', this.editConnectionForm.value.url);
    console.log('API Key: ', this.editConnectionForm.value.apiKey);
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
