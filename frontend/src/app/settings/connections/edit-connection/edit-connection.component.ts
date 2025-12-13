import {UpperCasePipe} from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  effect,
  ElementRef,
  inject,
  input,
  signal,
  viewChild,
  ViewContainerRef,
} from '@angular/core';
import {applyEach, Field, form, maxLength, minLength, pattern, readonly, required, schema} from '@angular/forms/signals';
import {Router} from '@angular/router';
import {ArrType, ConnectionCreate, MonitorType, PathMappingCreate} from 'src/app/models/connection';
import {ConnectionService} from 'src/app/services/connection.service';
import {HelpLinkIconComponent} from 'src/app/shared/help-link-icon/help-link-icon.component';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {PathSelectDialogComponent} from 'src/app/shared/path-select-dialog/path-select-dialog.component';

const pathMappingSchema = schema<PathMappingCreate>((schema) => {
  readonly(schema.path_from);
  required(schema.path_from, {message: 'Path From is required.'});
  required(schema.path_to, {message: 'Path To is required.'});
});

@Component({
  selector: 'app-edit-connection2',
  imports: [Field, HelpLinkIconComponent, LoadIndicatorComponent, UpperCasePipe],
  templateUrl: './edit-connection.component.html',
  styleUrl: './edit-connection.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditConnectionComponent {
  //#region In-built Injectors
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  private readonly router = inject(Router);
  private readonly viewContainerRef = inject(ViewContainerRef);
  //#endregion

  //#region Custom Injectors
  private readonly connectionService = inject(ConnectionService);
  //#endregion

  //#region Component Inputs
  connectionId = input(0, {
    transform: (value: any) => {
      const num = Number(value);
      return isNaN(num) ? -1 : num;
    },
  });
  //#endregion

  // #region Constants
  readonly arrOptions: ArrType[] = [ArrType.Radarr, ArrType.Sonarr];
  readonly monitorOptions: MonitorType[] = [MonitorType.Missing, MonitorType.New, MonitorType.None, MonitorType.Sync];
  //#endregion

  //#region Signals in Component
  connectionCreate = signal<ConnectionCreate>({
    api_key: '',
    arr_type: ArrType.Radarr,
    monitor: MonitorType.New,
    name: '',
    path_mappings: [],
    url: '',
    external_url: '',
  });
  arePathMappingsAdded = signal(false);
  isCreate = signal(false);
  isConnectionTested = signal(false);
  isReadyToSubmit = signal(false);
  isSubmitting = signal(false);
  submitResult = signal<string>('');

  connectionForm = form(this.connectionCreate, (schema) => {
    required(schema.api_key, {message: 'API Key is required.'});
    pattern(schema.api_key, /^[a-zA-Z0-9]*$/, {message: 'API Key must be alphanumeric.'});
    minLength(schema.api_key, 32, {message: 'API Key must be at least 32 characters long.'});
    maxLength(schema.api_key, 50, {message: 'API Key cannot be longer than 50 characters.'});
    required(schema.arr_type, {message: 'ARR Type is required.'});
    required(schema.monitor, {message: 'Monitor Type is required.'});
    required(schema.name, {message: 'Connection Name is required.'});
    minLength(schema.name, 3, {message: 'Connection Name must be at least 3 characters long.'});
    required(schema.url, {message: 'URL is required.'});
    minLength(schema.url, 5, {message: 'URL must be at least 5 characters long.'});
    pattern(schema.url, /^https?:\/\/.*/, {message: 'URL must start with http:// or https://.'});
    pattern(schema.external_url, /^https?:\/\/.*/, {message: 'External URL must start with http:// or https://.'});
    applyEach(schema.path_mappings, pathMappingSchema);
  });
  //#endregion

  //#region Signals from Service
  connection = this.connectionService.selectedConnection;
  isLoading = this.connectionService.connectionsResource.isLoading;
  //#endregion

  //#region Effects for reactivity
  connectionIDeffect = effect(() => {
    const id = this.connectionId();
    if (this.isLoading()) {
      console.log('Connection data is still loading. Waiting for it to complete.');
      return; // Wait until the connection data is loaded
    }
    if (id == -1) {
      this.isCreate.set(true);
    } else if (!this.connectionService.connectionExists(id)) {
      console.warn(`Connection with ID '${id}' does not exist. Redirecting to connections list.`);
      this.router.navigate(['/settings/connections']);
      return;
    }
    this.connectionService.connectionID.set(id);
  });
  connectionEffect = effect(() => {
    if (this.isSubmitting()) return; // Do not reset form if submitting
    const conn = this.connection();
    if (conn && !this.isSubmitting()) {
      this.connectionCreate.set(conn);
      this.isCreate.set(conn.id === -1);
      this.isConnectionTested.set(false);
      this.isReadyToSubmit.set(false);
      this.arePathMappingsAdded.set(conn.path_mappings.length > 0);
      this.submitResult.set('');
      this.changeDetectorRef.markForCheck();
    }
  });
  //#endregion

  // #region Form Methods

  formatPathFrom(pathFrom: string): string {
    // Ensure path_from ends with a slash or backslash
    if (pathFrom.endsWith('/') || pathFrom.endsWith('\\')) {
      return pathFrom; // Already formatted
    }
    // If it contains a slash, add a trailing slash
    if (pathFrom.includes('/')) {
      return pathFrom + '/';
    }
    // If it contains a backslash, add a trailing backslash
    if (pathFrom.includes('\\')) {
      return pathFrom + '\\';
    }
    // If it doesn't contain either, return as is (or you can choose to add a default slash)
    return pathFrom; // No change needed
  }

  // Figure out why path mappings are not updating in the form array
  // Also, submit result is not updating in the view
  addPathMappings(rootfolders: string[]) {
    let isUpdated = false;
    let count = 0;
    const pathMappings = this.connectionCreate().path_mappings;
    let newPathMappings: PathMappingCreate[] = [];
    rootfolders.forEach((rf) => {
      // Only add if no existing mapping with this path_from
      const formattedPathFrom = this.formatPathFrom(rf);
      const exists = pathMappings.some((pm) => pm.path_from === formattedPathFrom);
      if (!exists) {
        newPathMappings.push({id: null, connection_id: null, path_from: formattedPathFrom, path_to: ''});
        isUpdated = true;
        count++;
      }
    });
    this.connectionCreate.update((conn) => {
      conn.path_mappings = [...conn.path_mappings, ...newPathMappings];
      return {...conn};
    });
    if (isUpdated) {
      this.arePathMappingsAdded.set(true);
      // this.changeDetectorRef.markForCheck();
      let msg = `Retrieved ${rootfolders.length} root folders.`;
      msg += `\nAdded ${count} new root folders to Path Mappings.`;
      msg += `\nPlease update and test the connection to submit!`;
      if (rootfolders.length === 1) {
        msg = msg.replace('root folders.', 'root folder.');
      }
      if (count === 1) {
        msg = msg.replace('new root folders', 'new root folder');
      }

      this.submitResult.update((val) => `${val}\n${msg}`);
    } else {
      this.isConnectionTested.set(true);
      this.arePathMappingsAdded.set(true);
      this.isReadyToSubmit.set(true);
      this.submitResult.update((val) => {
        let res =
          val +
          `\nRetrieved ${rootfolders.length} root folders that were already in Path Mappings.` +
          '\nYou can now submit the connection.';
        if (rootfolders.length === 1) {
          res = res.replace('root folders that were ', 'root folder that was ');
        }
        return res;
      });
    }
    console.log('Path Mappings after adding root folders:', this.connectionCreate());
  }

  removePathMapping(index: number) {
    let pathMappings = this.connectionCreate().path_mappings;
    const newPathMappings = pathMappings.filter((_, i) => i !== index);
    this.connectionCreate.update((conn) => {
      conn.path_mappings = newPathMappings;
      return {...conn};
    });
    // this.connectionForm!.markAsTouched(); ? not sure how to do this with signal forms
    // this.connectionForm!.markAsDirty();
  }

  // #endregion

  // #region Dialogs
  private readonly cancelDialog = viewChild<ElementRef<HTMLDialogElement>>('cancelDialog');
  private readonly deleteDialog = viewChild<ElementRef<HTMLDialogElement>>('deleteConnectionDialog');
  protected closeDeleteDialog = () => this.deleteDialog()?.nativeElement.close();
  protected showDeleteDialog = () => this.deleteDialog()?.nativeElement.showModal();
  protected closeCancelDialog = () => this.cancelDialog()?.nativeElement.close();
  protected showCancelDialog = () => this.cancelDialog()?.nativeElement.showModal();

  openPathSelectDialog(index: number): void {
    const path_from = this.connectionCreate().path_mappings[index].path_from;
    // Open the dialog for selecting a path value
    const dialogRef = this.viewContainerRef.createComponent(PathSelectDialogComponent);
    dialogRef.setInput('name', path_from);
    dialogRef.setInput('path', path_from);
    dialogRef.setInput('pathShouldEndWith', '/');
    dialogRef.instance.onSubmit.subscribe((emitValue: string) => {
      if (emitValue) {
        // Update the path_to value in the form array
        this.connectionForm.path_mappings[index].path_to().setControlValue(emitValue);
      }
      // Else, dialog closed without submission, do nothing
      setTimeout(() => {
        dialogRef.destroy(); // Destroy the dialog component after use
      }, 500);
    });
  }
  // #endregion

  // #region Action Methods
  checkConnectionValidity() {
    if (!this.connectionForm().valid()) {
      // console.log('Form is invalid, cannot submit.', this.connectionForm);
      this.submitResult.set('Form is invalid, please correct the errors and try again.');
      return false;
    }
    return true;
  }
  onCancel() {
    // Ask Confirmation if form changed, else go back
    if (this.connectionForm().dirty()) {
      this.showCancelDialog();
    } else {
      this.router.navigate(['/settings/connections']);
    }
  }
  onConfirmCancel() {
    // Close the dialog and go back
    this.closeCancelDialog();
    this.router.navigate(['/settings/connections']);
  }
  onConfirmDelete() {
    // Close the dialog and delete the connection
    this.closeDeleteDialog();
    this.deleteConnection();
  }
  onSubmit($event: Event) {
    $event.preventDefault();
    if (!this.checkConnectionValidity()) return;
    // Check if connection is tested and ready to submit
    if (!this.isConnectionTested() || !this.isReadyToSubmit()) {
      this.testConnection();
      return;
    }
    // Make sure Connection is ready to submit
    if (!this.isReadyToSubmit()) {
      this.submitResult.set('Please test the connection before submitting.');
      return;
    }
    // Ready to Submit, either create or update
    // let connectionData = this.connectionForm!.value;
    if (this.isCreate()) {
      // Create new connection
      // console.log('Creating new connection', connectionData);
      this.createConnection();
      return;
    }
    // Update existing connection
    // console.log('Form Submitted', connectionData);
    this.updateConnection();
    // this.connectionService.updateConnection(this.connectionForm!.value);
    return;
  }
  // #endregion

  // #region Submission Methods
  createConnection() {
    if (!this.checkConnectionValidity()) return;
    if (!this.isReadyToSubmit() || this.isSubmitting()) return;
    this.isSubmitting.set(true);
    this.submitResult.set('Creating connection, please wait...');
    let connectionData = this.connectionCreate();
    // console.log('Create connection: ', connectionData);
    this.connectionService.addConnection(connectionData).subscribe({
      next: (result) => {
        this.submitResult.set(result);
        setTimeout(() => {
          this.router.navigate(['/settings/connections']).then(() => {
            this.connectionService.connectionsResource.reload();
          });
        }, 3000);
      },
      error: (error) => {
        console.error('Error creating connection:', error);
        this.submitResult.set(`Error creating connection: ${error.message || error}. Try again in some time`);
      },
    });
  }
  deleteConnection() {
    if (!this.connectionService.connectionExists(this.connectionId())) return;
    this.connectionService.deleteConnection(this.connectionId()).subscribe({
      next: (result) => {
        this.submitResult.set(`Connection deleted successfully: ${result}`);
        this.connectionService.connectionsResource.reload();
        setTimeout(() => {
          this.router.navigate(['/settings/connections']).then(() => {
            this.connectionService.connectionsResource.reload();
          });
        }, 3000);
      },
      error: (error) => {
        console.error('Error deleting connection:', error);
        this.submitResult.set(`Error deleting connection: ${error.message || error}. Try again in some time`);
      },
    });
  }
  getRootFolders() {
    if (!this.checkConnectionValidity()) return;
    if (this.isReadyToSubmit()) {
      return;
    }
    let connectionData = this.connectionCreate();
    // console.log('Getting root folders with data', connectionData);
    this.connectionService.getRootFolders(connectionData).subscribe({
      next: (result) => {
        if (Array.isArray(result)) {
          this.arePathMappingsAdded.set(true);
          // this.submitResult.update((val) => `${val}\nFound ${result.length} root folder(s), adding to Path Mappings...`);
          this.addPathMappings(result);
        } else {
          this.arePathMappingsAdded.set(false);
          this.submitResult.update((val) => `${val}\nError getting root folders: ${result}`);
        }
      },
      error: (error) => {
        console.error('Error fetching root folders:', error);
        this.submitResult.update((val) => `${val}\nError fetching root folders: ${error.message || error}. Try again in some time`);
      },
    });
  }
  testConnection() {
    if (!this.checkConnectionValidity()) return;
    let connectionData = this.connectionCreate();
    // console.log('Testing connection with data', connectionData);
    this.connectionService.testConnection(connectionData).subscribe({
      next: (result) => {
        this.submitResult.set(result);
        if (result.toLowerCase().includes('success')) {
          // Test was successful
          if (!this.isConnectionTested()) {
            // First test is for initial connection -> get rootfolders
            this.isConnectionTested.set(true);
            this.getRootFolders();
          } else {
            // Second test is for Connection with path mappings -> mark for submission
            this.isReadyToSubmit.set(true);
            this.submitResult.update((val) => `${val}\nConnection tested successfully. You can now submit the connection.`);
          }
        }
      },
      error: (error) => {
        console.error('Error testing connection:', error);
        this.submitResult.set(`Error testing connection: ${error.message || error}. Try again in some time`);
      },
    });
  }
  updateConnection() {
    if (!this.checkConnectionValidity()) return;
    if (!this.isReadyToSubmit() || this.isSubmitting()) return;
    this.isSubmitting.set(true);
    this.submitResult.set('Updating connection, please wait...');
    let connectionData = this.connectionCreate();
    // console.log('Update connection: ', connectionData);
    this.connectionService.updateConnection(this.connectionId(), connectionData).subscribe({
      next: (result) => {
        this.submitResult.set(result);
        setTimeout(() => {
          this.router.navigate(['/settings/connections']).then(() => {
            this.connectionService.connectionsResource.reload();
          });
        }, 3000);
      },
      error: (error) => {
        console.error('Error updating connection:', error);
        this.submitResult.set(`Error updating connection: ${error.message || error}. Try again in some time`);
      },
    });
  }
  // #endregion Submission Methods
}
