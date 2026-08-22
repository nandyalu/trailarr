import {HttpClient, httpResource} from '@angular/common/http';
import {computed, inject, Injectable, signal} from '@angular/core';
import {catchError, Observable} from 'rxjs';
import {ArrType, ConnectionCreate, ConnectionRead, ConnectionUpdate} from 'src/app/models/connection';
import {DoctorReport, SuggestedMapping} from 'src/app/models/diagnostics';
import {environment} from 'src/environment';
import {handleError} from './utils';
import {WebsocketService} from './websocket.service';

@Injectable({
  providedIn: 'root',
})
export class ConnectionService {
  private readonly http = inject(HttpClient);
  private readonly websocketService = inject(WebsocketService);

  private connectionsUrl = environment.apiUrl + environment.connections;

  readonly connectionsResource = httpResource<ConnectionRead[]>(() => ({url: this.connectionsUrl}), {
    defaultValue: [],
  });

  private readonly newConnection = {
    added_at: new Date().toISOString(),
    api_key: '',
    arr_type: ArrType.Radarr,
    id: -1,
    monitor_new_media: true,
    name: '',
    machine_identifier: null,
    path_mappings: [],
    url: '',
    external_url: '',
  } as ConnectionRead;

  /**
   * Signal to track the currently selected connection ID
   * - Set to `-1` to get a new Connection
   */
  readonly connectionID = signal<number>(-1); // '-1' means create new

  /**
   * A computed signal that returns the currently selected connection.
   * @returns `ConnectionRead`
   * - connection with the current `connectionID` if it exists
   * - a new connection instance if it doesn't
   */
  readonly selectedConnection = computed(() => {
    const connection = this.connectionsResource.value().find((conn) => conn.id === this.connectionID());
    return connection ? connection : this.newConnection;
  });

  addConnection(connection: ConnectionCreate): Observable<string> {
    return this.http.post<string>(this.connectionsUrl, connection).pipe(catchError(handleError()));
  }

  connectionExists(id: number): boolean {
    const exists = this.connectionsResource.value().some((conn) => conn.id === id);
    if (exists) return true; // Connection exists in the local list
    // Else, send a notification that connection does not exist
    if (id != -1) this.websocketService.showToast(`Connection with ID '${id}' does not exist.`, 'error');
    return false;
  }

  deleteConnection(id: number): Observable<string> {
    var connectionIdUrl = this.connectionsUrl + id;
    return this.http.delete<string>(connectionIdUrl).pipe(catchError(handleError()));
  }

  /** Last Connection Doctor report per checked connection. The backend
   * keeps these on disk, so they survive a restart. */
  readonly doctorReportsResource = httpResource<DoctorReport[]>(() => ({url: this.connectionsUrl + 'doctor'}), {
    defaultValue: [],
  });

  /** Run the doctor for every connection at once. */
  runAllDoctors(): Observable<DoctorReport[]> {
    return this.http.post<DoctorReport[]>(`${this.connectionsUrl}doctor/run-all`, {}).pipe(catchError(handleError()));
  }

  runDoctor(id: number): Observable<DoctorReport> {
    return this.http.post<DoctorReport>(`${this.connectionsUrl}${id}/doctor`, {}).pipe(catchError(handleError()));
  }

  applyDoctorMapping(id: number, mapping: SuggestedMapping): Observable<DoctorReport> {
    return this.http.post<DoctorReport>(`${this.connectionsUrl}${id}/doctor/mappings`, mapping).pipe(catchError(handleError()));
  }

  getRootFolders(connection: ConnectionCreate): Observable<string[] | string> {
    var rootFoldersUrl = this.connectionsUrl + 'rootfolders';
    return this.http.post<string[]>(rootFoldersUrl, connection).pipe(catchError(handleError()));
  }

  testConnection(connection: ConnectionCreate): Observable<string> {
    var testConnectionUrl = this.connectionsUrl + 'test';
    return this.http.post<string>(testConnectionUrl, connection).pipe(catchError(handleError()));
  }

  updateConnection(id: number, connection: ConnectionUpdate): Observable<string> {
    var connectionIdUrl = this.connectionsUrl + id;
    return this.http.put<string>(connectionIdUrl, connection).pipe(catchError(handleError()));
  }
}
