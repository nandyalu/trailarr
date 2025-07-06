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
import {FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {Router} from '@angular/router';
import {ArrType, ConnectionRead, MonitorType, PathMappingCru} from 'generated-sources/openapi';
import {ConnectionService} from 'src/app/services/connection.service';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {PathSelectDialogComponent} from 'src/app/shared/path-select-dialog/path-select-dialog.component';

@Component({
  selector: 'app-edit-connection2',
  imports: [LoadIndicatorComponent, ReactiveFormsModule, UpperCasePipe],
  templateUrl: './edit-connection.component.html',
  styleUrl: './edit-connection.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditConnectionComponent {
  //#region In-built Injectors
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  private readonly formBuilder = inject(FormBuilder);
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
  connectionForm = undefined as FormGroup | undefined;
  //#endregion

  //#region Signals in Component
  arePathMappingsAdded = signal(false);
  isCreate = signal(false);
  isConnectionTested = signal(false);
  isReadyToSubmit = signal(false);
  isSubmitting = signal(false);
  submitResult = signal<string>('');
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
      this.createForm(conn);
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
  formatPathFrom(path_from: string): string {
    // Ensure path_from ends with a slash or backslash
    if (path_from.endsWith('/') || path_from.endsWith('\\')) {
      return path_from; // Already formatted
    }
    // If it contains a slash, add a trailing slash
    if (path_from.includes('/')) {
      return path_from + '/';
    }
    // If it contains a backslash, add a trailing backslash
    if (path_from.includes('\\')) {
      return path_from + '\\';
    }
    // If it doesn't contain either, return as is (or you can choose to add a default slash)
    return path_from; // No change needed
  }

  addPathMappings(rootfolders: string[]) {
    if (!this.connectionForm) return;
    const path_mappings = this.connectionForm.get('path_mappings') as FormArray;
    if (!path_mappings) return;
    let isUpdated = false;
    let count = 0;
    rootfolders.forEach((rf) => {
      // Only add if no existing mapping with this path_from
      const exists = path_mappings.controls.some((ctrl) => ctrl.get('path_from')?.value === this.formatPathFrom(rf));
      if (!exists) {
        path_mappings.push(this.createPathMapping(null, rf));
        isUpdated = true;
        count++;
      }
    });
    if (isUpdated) {
      this.arePathMappingsAdded.set(true);
      this.changeDetectorRef.markForCheck();
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
  }

  createForm(connection: ConnectionRead) {
    this.connectionForm = this.formBuilder.group({
      added_at: [connection.added_at],
      api_key: [
        connection.api_key,
        [Validators.required, Validators.pattern('^[a-zA-Z0-9]*$'), Validators.minLength(32), Validators.maxLength(50)],
      ],
      arr_type: [connection.arr_type, Validators.required],
      id: [connection.id > 0 ? connection.id : null],
      monitor: [connection.monitor, Validators.required],
      name: [connection.name, [Validators.required, Validators.minLength(3)]],
      path_mappings: this.createPathMappings(connection),
      url: [connection.url, [Validators.required, Validators.pattern('https?://.*'), Validators.minLength(10)]],
    });
  }

  createPathMapping(pathMapping: PathMappingCru | null = null, pathFrom: string = '') {
    let id = null;
    if (pathMapping && pathMapping.id && pathMapping.id > 0) {
      id = pathMapping.id;
    }
    let pathFromFormatted = pathMapping ? pathMapping.path_from : pathFrom;
    if (!pathFromFormatted) {
      pathFromFormatted = ''; // Ensure it's not undefined
    }
    pathFromFormatted = this.formatPathFrom(pathFromFormatted); // Format the path_from
    return this.formBuilder.group({
      id: [id],
      connection_id: [pathMapping ? pathMapping.connection_id : null],
      path_from: [pathFromFormatted, Validators.required],
      path_to: [pathMapping ? pathMapping.path_to : '', Validators.required],
    });
  }

  createPathMappings(connection: ConnectionRead) {
    return this.formBuilder.array(connection.path_mappings.map((pm) => this.createPathMapping(pm)));
  }

  get pathMappings(): FormArray {
    return this.connectionForm!.get('path_mappings') as FormArray;
  }

  removePathMapping(index: number) {
    this.pathMappings.removeAt(index);
    this.connectionForm!.markAsTouched();
    this.connectionForm!.markAsDirty();
  }

  // #endregion

  // #region Dialogs
  private readonly cancelDialog = viewChild<ElementRef<HTMLDialogElement>>('cancelDialog');
  private readonly deleteDialog = viewChild<ElementRef<HTMLDialogElement>>('deleteConnectionDialog');
  protected closeDeleteDialog = () => this.deleteDialog()?.nativeElement.close();
  protected showDeleteDialog = () => this.deleteDialog()?.nativeElement.showModal();
  protected closeCancelDialog = () => this.cancelDialog()?.nativeElement.close();
  protected showCancelDialog = () => this.cancelDialog()?.nativeElement.showModal();

  openPathSelectDialog(index: number, path_from: string): void {
    // Open the dialog for selecting a path value
    const dialogRef = this.viewContainerRef.createComponent(PathSelectDialogComponent);
    dialogRef.setInput('name', path_from);
    dialogRef.setInput('path', path_from);
    dialogRef.setInput('pathShouldEndWith', '/');
    dialogRef.instance.onSubmit.subscribe((emitValue: string) => {
      if (emitValue) {
        // Submit the value back to caller
        this.pathMappings.at(index).get('path_to')?.setValue(emitValue);
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
    if (!this.connectionForm!.valid) {
      // console.log('Form is invalid, cannot submit.', this.connectionForm);
      this.submitResult.set('Form is invalid, please correct the errors and try again.');
      return false;
    }
    return true;
  }
  onCancel() {
    // Ask Confirmation if form changed, else go back
    if (!this.connectionForm!.pristine) {
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
  onSubmit() {
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
    let connectionData = this.connectionForm!.value;
    // console.log('Create connection: ', connectionData);
    this.connectionService.addConnection(connectionData).subscribe({
      next: (result) => {
        this.submitResult.set(result);
        setTimeout(() => {
          this.router.navigate(['/settings/connections']).then(() => {
            this.connectionService.connectionsResource.reload();
          });
        }, 2000);
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
        }, 2000);
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
    let connectionData = this.connectionForm!.value;
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
    let connectionData = this.connectionForm!.value;
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
    let connectionData = this.connectionForm!.value;
    // console.log('Update connection: ', connectionData);
    this.connectionService.updateConnection(this.connectionId(), connectionData).subscribe({
      next: (result) => {
        this.submitResult.set(result);
        setTimeout(() => {
          this.router.navigate(['/settings/connections']).then(() => {
            this.connectionService.connectionsResource.reload();
          });
        }, 2000);
      },
      error: (error) => {
        console.error('Error updating connection:', error);
        this.submitResult.set(`Error updating connection: ${error.message || error}. Try again in some time`);
      },
    });
  }
  // #endregion Submission Methods
}
