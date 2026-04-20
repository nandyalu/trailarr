import {UpperCasePipe} from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  effect,
  ElementRef,
  inject,
  input,
  OnDestroy,
  signal,
  viewChild,
  ViewContainerRef,
} from '@angular/core';
import {interval, Subscription, switchMap, takeWhile} from 'rxjs';
import {Router} from '@angular/router';
import {ArrType, ConnectionCreate, MonitorType, PathMappingCreate} from 'src/app/models/connection';
import {ConnectionService} from 'src/app/services/connection.service';
import {PlexOAuthService} from 'src/app/services/plex-oauth.service';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {PathSelectDialogComponent} from 'src/app/shared/path-select-dialog/path-select-dialog.component';

type OAuthState = 'idle' | 'pending_pin' | 'pending_auth' | 'server_select' | 'authenticated' | 'error';

@Component({
  selector: 'app-edit-plex-connection',
  imports: [LoadIndicatorComponent, UpperCasePipe],
  templateUrl: './edit-plex-connection.component.html',
  styleUrl: './edit-plex-connection.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditPlexConnectionComponent implements OnDestroy {
  //#region Injectors
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly router = inject(Router);
  private readonly viewContainerRef = inject(ViewContainerRef);
  private readonly connectionService = inject(ConnectionService);
  private readonly plexOAuth = inject(PlexOAuthService);
  //#endregion

  //#region Inputs
  connectionId = input(0, {
    transform: (value: any) => {
      const num = Number(value);
      return isNaN(num) ? -1 : num;
    },
  });
  //#endregion

  //#region Constants
  readonly monitorOptions: MonitorType[] = [MonitorType.Missing, MonitorType.New, MonitorType.None, MonitorType.Sync];
  //#endregion

  //#region Dialog refs
  private readonly deleteDialog = viewChild<ElementRef<HTMLDialogElement>>('deleteConnectionDialog');
  //#endregion

  //#region OAuth State
  oauthState = signal<OAuthState>('idle');
  errorMessage = signal<string>('');
  /** Flat list of (label, uri) options for the server-selection dropdown */
  serverUriOptions = signal<{label: string; uri: string}[]>([]);
  selectedServerUri = signal<string>('');
  private clientId = '';
  private pinId = 0;
  private plexToken = '';
  private selectedServerName = '';
  private popupWindow: Window | null = null;
  private pollSub?: Subscription;
  //#endregion

  //#region Connection form state
  isCreate = signal(false);
  isLoading = this.connectionService.connectionsResource.isLoading;
  isPathMappingsLoaded = signal(false);
  isReadyToSubmit = signal(false);
  isSubmitting = signal(false);
  submitResult = signal<string>('');
  /** Cache of Plex library folders fetched during test — used by Add Library Folders button */
  fetchedLibraryFolders = signal<string[]>([]);

  connectionData = signal<ConnectionCreate>({
    name: '',
    arr_type: ArrType.Plex,
    url: '',
    external_url: '',
    api_key: '',
    monitor: MonitorType.New,
    path_mappings: [],
  });
  selectedMonitor = signal<MonitorType>(MonitorType.New);
  //#endregion

  //#region Computed helpers
  hasEmptyPathTo(): boolean {
    return this.connectionData().path_mappings.some((pm) => !pm.path_to.trim());
  }

  //#endregion

  //#region Effects
  connectionIdEffect = effect(() => {
    const id = this.connectionId();
    if (this.isLoading()) return;
    if (id === -1) {
      this.isCreate.set(true);
    } else if (!this.connectionService.connectionExists(id)) {
      this.router.navigate(['/settings/connections']);
      return;
    }
    this.connectionService.connectionID.set(id);
  });

  connectionEffect = effect(() => {
    if (this.isSubmitting()) return;
    const conn = this.connectionService.selectedConnection();
    if (conn && conn.arr_type === ArrType.Plex) {
      this.connectionData.set(conn);
      this.selectedMonitor.set(conn.monitor);
      this.isCreate.set(conn.id === -1);
      this.oauthState.set('authenticated');
      this.isPathMappingsLoaded.set(conn.path_mappings.length > 0);
      this.isReadyToSubmit.set(false);
      this.submitResult.set('');
      this.cdr.markForCheck();
    }
  });
  //#endregion

  ngOnDestroy() {
    this._stopPolling();
  }

  // ----------------------------------------------------------------
  // OAuth flow
  // ----------------------------------------------------------------

  startOAuth() {
    this.oauthState.set('pending_pin');
    this.errorMessage.set('');
    this.clientId = `trailarr_${Date.now()}`;

    this.plexOAuth.requestPin(this.clientId).subscribe({
      next: (pin) => {
        this.pinId = pin.id;
        const authUrl = this.plexOAuth.buildAuthUrl(pin.code, this.clientId);
        this.oauthState.set('pending_auth');
        this.popupWindow = window.open(authUrl, 'PlexAuth', 'width=600,height=750,scrollbars=yes');
        this._startPolling();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.oauthState.set('error');
        this.errorMessage.set(`Failed to start Plex auth: ${err.message ?? err}`);
        this.cdr.markForCheck();
      },
    });
  }

  private _startPolling() {
    this.pollSub = interval(2000)
      .pipe(
        switchMap(() => this.plexOAuth.pollPin(this.pinId, this.clientId)),
        takeWhile((pin) => pin.authToken === null, true),
      )
      .subscribe({
        next: (pin) => {
          if (pin.authToken) {
            this._stopPolling();
            this.plexToken = pin.authToken;
            this._fetchServers();
          }
        },
        error: (err) => {
          this._stopPolling();
          this.oauthState.set('error');
          this.errorMessage.set(`Plex auth polling failed: ${err.message ?? err}`);
          this.cdr.markForCheck();
        },
      });
  }

  private _stopPolling() {
    this.pollSub?.unsubscribe();
    this.pollSub = undefined;
    if (this.popupWindow && !this.popupWindow.closed) {
      this.popupWindow.close();
      this.popupWindow = null;
    }
  }

  private _fetchServers() {
    this.plexOAuth.getServers(this.plexToken, this.clientId).subscribe({
      next: (servers) => {
        const options = servers.flatMap((s) =>
          s.uris.map((uri) => ({
            label: s.uris.length > 1 ? `${s.name} — ${uri}` : s.name,
            uri,
            serverName: s.name,
          })),
        );
        if (options.length === 0) {
          this.oauthState.set('error');
          this.errorMessage.set('No Plex Media Servers found for this account.');
        } else if (options.length === 1) {
          this._applyUri(options[0].serverName, options[0].uri);
        } else {
          this.serverUriOptions.set(options);
          this.selectedServerUri.set(options[0].uri);
          this.selectedServerName = options[0].serverName;
          this.oauthState.set('server_select');
        }
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.oauthState.set('error');
        this.errorMessage.set(`Could not fetch servers: ${err.message ?? err}`);
        this.cdr.markForCheck();
      },
    });
  }

  setSelectedServerUri(event: Event) {
    const uri = (event.target as HTMLSelectElement).value;
    this.selectedServerUri.set(uri);
    const opt = this.serverUriOptions().find((o) => o.uri === uri);
    this.selectedServerName = (opt as any)?.serverName ?? '';
  }

  applySelectedServer() {
    this._applyUri(this.selectedServerName, this.selectedServerUri());
  }

  private _applyUri(serverName: string, uri: string) {
    this.connectionData.update((d) => ({
      ...d,
      url: uri,
      api_key: this.plexToken,
      name: d.name || serverName,
    }));
    this.oauthState.set('authenticated');
    this.isReadyToSubmit.set(false);
    this.cdr.markForCheck();
  }

  reconnect() {
    this.oauthState.set('idle');
    this.plexToken = '';
    this.connectionData.update((d) => ({...d, url: '', api_key: ''}));
    this.isPathMappingsLoaded.set(false);
    this.isReadyToSubmit.set(false);
    this.submitResult.set('');
  }

  // ----------------------------------------------------------------
  // Form helpers
  // ----------------------------------------------------------------

  setName(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.connectionData.update((d) => ({...d, name: value}));
  }

  setMonitor(monitor: MonitorType) {
    this.selectedMonitor.set(monitor);
    this.connectionData.update((d) => ({...d, monitor}));
    this.isReadyToSubmit.set(false);
  }

  formatPathFrom(path: string): string {
    if (path.endsWith('/') || path.endsWith('\\')) return path;
    if (path.includes('/')) return path + '/';
    if (path.includes('\\')) return path + '\\';
    return path;
  }

  addPathMappings(rootfolders: string[]) {
    const existing = this.connectionData().path_mappings;
    const toAdd: PathMappingCreate[] = [];
    for (const rf of rootfolders) {
      const formatted = this.formatPathFrom(rf);
      if (!existing.some((pm) => pm.path_from === formatted)) {
        toAdd.push({id: null, connection_id: null, path_from: formatted, path_to: ''});
      }
    }
    if (toAdd.length > 0) {
      this.connectionData.update((d) => ({...d, path_mappings: [...d.path_mappings, ...toAdd]}));
      this.isPathMappingsLoaded.set(true);
      this.submitResult.set(
        `Retrieved ${rootfolders.length} library folder(s). Added ${toAdd.length} new folder(s). Fill in the local paths then test and save.`,
      );
    } else {
      this.isPathMappingsLoaded.set(true);
      this.isReadyToSubmit.set(true);
      this.submitResult.set('All library folders already configured. You can now save the connection.');
    }
    this.cdr.markForCheck();
  }

  updatePathTo(index: number, event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.connectionData.update((d) => {
      const mappings = [...d.path_mappings];
      mappings[index] = {...mappings[index], path_to: value};
      return {...d, path_mappings: mappings};
    });
    this.isReadyToSubmit.set(false);
  }

  removePathMapping(index: number) {
    this.connectionData.update((d) => {
      const mappings = d.path_mappings.filter((_, i) => i !== index);
      return {...d, path_mappings: mappings};
    });
    this.isReadyToSubmit.set(false);
  }

  addLibraryFolders() {
    const cached = this.fetchedLibraryFolders();
    if (cached.length > 0) {
      this.addPathMappings(cached);
    } else {
      this._loadPathMappings(this.connectionData());
    }
  }

  openPathSelectDialog(index: number) {
    const pathFrom = this.connectionData().path_mappings[index].path_from;
    const dialogRef = this.viewContainerRef.createComponent(PathSelectDialogComponent);
    dialogRef.setInput('name', pathFrom);
    dialogRef.setInput('path', pathFrom);
    dialogRef.setInput('pathShouldEndWith', '/');
    dialogRef.instance.onSubmit.subscribe((value: string) => {
      if (value) {
        this.connectionData.update((d) => {
          const mappings = [...d.path_mappings];
          mappings[index] = {...mappings[index], path_to: value};
          return {...d, path_mappings: mappings};
        });
        this.isReadyToSubmit.set(false);
      }
      setTimeout(() => dialogRef.destroy(), 500);
    });
  }

  // ----------------------------------------------------------------
  // Test / submit actions
  // ----------------------------------------------------------------

  onCancel() {
    this.router.navigate(['/settings/connections']);
  }

  testConnection() {
    const data = this.connectionData();
    if (!data.url || !data.api_key) {
      this.submitResult.set('Complete the Plex authentication first.');
      return;
    }
    this.submitResult.set('Testing connection…');
    this.connectionService.testConnection(data).subscribe({
      next: (result) => {
        this.submitResult.set(result);
        if (result.toLowerCase().includes('connected')) {
          if (!this.isPathMappingsLoaded()) {
            this._loadPathMappings(data);
          } else {
            this.isReadyToSubmit.set(true);
            this.submitResult.update((v) => v + '\nConnection OK. You can now save.');
          }
        }
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.submitResult.set(`Connection test failed: ${err.message ?? err}`);
        this.cdr.markForCheck();
      },
    });
  }

  private _loadPathMappings(data: ConnectionCreate) {
    this.connectionService.getRootFolders(data).subscribe({
      next: (folders) => {
        if (Array.isArray(folders)) {
          this.fetchedLibraryFolders.set(folders);
          this.addPathMappings(folders);
        }
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.submitResult.update((v) => v + `\nCould not fetch library folders: ${err.message ?? err}`);
        this.cdr.markForCheck();
      },
    });
  }

  onSubmit() {
    const data = this.connectionData();
    if (!data.name || !data.url || !data.api_key) {
      this.submitResult.set('Please complete all required fields.');
      return;
    }
    if (this.hasEmptyPathTo()) {
      this.submitResult.set('All library paths must be filled in before saving.');
      return;
    }
    if (!this.isReadyToSubmit()) {
      this.testConnection();
      return;
    }
    if (this.isCreate()) {
      this._createConnection(data);
    } else {
      this._updateConnection(data);
    }
  }

  private _createConnection(data: ConnectionCreate) {
    this.isSubmitting.set(true);
    this.submitResult.set('Creating connection…');
    this.connectionService.addConnection(data).subscribe({
      next: () => {
        this.submitResult.set('Connection created successfully!');
        setTimeout(() => {
          this.router.navigate(['/settings/connections']).then(() => this.connectionService.connectionsResource.reload());
        }, 2000);
      },
      error: (err) => {
        this.isSubmitting.set(false);
        this.submitResult.set(`Error creating connection: ${err.message ?? err}`);
        this.cdr.markForCheck();
      },
    });
  }

  private _updateConnection(data: ConnectionCreate) {
    this.isSubmitting.set(true);
    this.submitResult.set('Saving changes…');
    this.connectionService.updateConnection(this.connectionId(), data).subscribe({
      next: () => {
        this.submitResult.set('Connection saved successfully!');
        setTimeout(() => {
          this.router.navigate(['/settings/connections']).then(() => this.connectionService.connectionsResource.reload());
        }, 2000);
      },
      error: (err) => {
        this.isSubmitting.set(false);
        this.submitResult.set(`Error saving connection: ${err.message ?? err}`);
        this.cdr.markForCheck();
      },
    });
  }

  // ----------------------------------------------------------------
  // Delete
  // ----------------------------------------------------------------

  showDeleteDialog() {
    this.deleteDialog()?.nativeElement.showModal();
  }

  closeDeleteDialog() {
    this.deleteDialog()?.nativeElement.close();
  }

  onConfirmDelete() {
    this.closeDeleteDialog();
    this.deleteConnection();
  }

  deleteConnection() {
    const id = this.connectionId();
    if (!this.connectionService.connectionExists(id)) return;
    this.connectionService.deleteConnection(id).subscribe({
      next: () => {
        this.router.navigate(['/settings/connections']);
      },
      error: (err) => {
        this.submitResult.set(`Error deleting connection: ${err.message ?? err}`);
        this.cdr.markForCheck();
      },
    });
  }
}
