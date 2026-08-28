import {CommonModule} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, inject, signal} from '@angular/core';
import {RouterLink} from '@angular/router';
import {firstValueFrom} from 'rxjs';
import {DoctorReport, ProbeStatus, SuggestedMapping} from 'src/app/models/diagnostics';
import {ConnectionService} from 'src/app/services/connection.service';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {RouteAdd, RouteConnections, RouteEdit, RoutePlex, RouteSettings} from 'src/routing';

@Component({
  selector: 'app-show-connections',
  templateUrl: './show-connections.component.html',
  styleUrl: './show-connections.component.scss',
  imports: [CommonModule, LoadIndicatorComponent, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ShowConnectionsComponent {
  private readonly connectionService = inject(ConnectionService);

  protected readonly connectionsResource = this.connectionService.connectionsResource;
  protected readonly isLoading = this.connectionsResource.isLoading;

  resultMessage = signal<string>('');
  resultType = signal<string>('');
  selectedId = 0;

  // ----- Connection Doctor -----
  protected readonly doctorReports = this.connectionService.doctorReportsResource;
  /** Connection id whose report is open in the detail dialog, or null. */
  protected readonly doctorConnectionId = signal<number | null>(null);
  /** Report shown in the dialog — kept fresh by run/apply responses. */
  protected readonly doctorDialogReport = signal<DoctorReport | null>(null);
  protected readonly doctorRunning = signal<boolean>(false);
  protected readonly doctorError = signal<string>('');
  /** True while "Check all" runs the doctor for every connection. */
  protected readonly checkingAll = signal<boolean>(false);

  protected readonly reportsById = computed(() => {
    const map = new Map<number, DoctorReport>();
    for (const report of this.doctorReports.value()) {
      map.set(report.connection_id, report);
    }
    return map;
  });

  protected doctorChip(connectionId: number): {label: string; state: string} {
    const report = this.reportsById().get(connectionId);
    if (!report) {
      return {label: 'NOT CHECKED', state: 'unknown'};
    }
    return report.status === 'healthy' ? {label: 'HEALTHY', state: 'healthy'} : {label: 'ISSUES FOUND', state: 'issues'};
  }

  /** Run the doctor for every connection — one click, not one dialog each. */
  protected async checkAllConnections(): Promise<void> {
    if (this.checkingAll()) return;
    this.checkingAll.set(true);
    this.resultMessage.set('');
    try {
      const reports = await firstValueFrom(this.connectionService.runAllDoctors());
      this.doctorReports.reload();
      const issues = reports.filter((r) => r.status !== 'healthy').length;
      this.resultMessage.set(
        issues === 0
          ? `Checked ${reports.length} connection(s) — all healthy.`
          : `Checked ${reports.length} connection(s) — ${issues} with issues. Click ISSUES FOUND on a connection to see the fix.`,
      );
      this.resultType.set(issues === 0 ? 'success' : 'error');
    } catch (error) {
      this.resultMessage.set('Could not run the checks. ' + ((error as Error).message ?? ''));
      this.resultType.set('error');
    } finally {
      this.checkingAll.set(false);
    }
  }

  protected async openDoctorDialog(connectionId: number, event: Event): Promise<void> {
    event.preventDefault();
    event.stopPropagation();
    this.doctorConnectionId.set(connectionId);
    this.doctorError.set('');
    const known = this.reportsById().get(connectionId) ?? null;
    this.doctorDialogReport.set(known);
    const dialog = document.getElementById('doctorDialog') as HTMLDialogElement | null;
    dialog?.showModal();
    if (!known) {
      await this.runDoctor();
    }
  }

  protected closeDoctorDialog(): void {
    const dialog = document.getElementById('doctorDialog') as HTMLDialogElement | null;
    dialog?.close();
    this.doctorConnectionId.set(null);
    this.doctorDialogReport.set(null);
  }

  protected async runDoctor(): Promise<void> {
    const id = this.doctorConnectionId();
    if (id === null || this.doctorRunning()) return;
    this.doctorRunning.set(true);
    this.doctorError.set('');
    try {
      const report = await firstValueFrom(this.connectionService.runDoctor(id));
      this.doctorDialogReport.set(report);
      this.doctorReports.reload();
    } catch (error) {
      this.doctorError.set('Check failed. ' + ((error as Error).message ?? ''));
    } finally {
      this.doctorRunning.set(false);
    }
  }

  protected async applyMapping(mapping: SuggestedMapping): Promise<void> {
    const id = this.doctorConnectionId();
    if (id === null || this.doctorRunning()) return;
    this.doctorRunning.set(true);
    this.doctorError.set('');
    try {
      const report = await firstValueFrom(this.connectionService.applyDoctorMapping(id, mapping));
      this.doctorDialogReport.set(report);
      this.doctorReports.reload();
      this.connectionsResource.reload();
    } catch (error) {
      this.doctorError.set('Could not apply the mapping. ' + ((error as Error).message ?? ''));
    } finally {
      this.doctorRunning.set(false);
    }
  }

  protected probeIcon(status: ProbeStatus): string {
    switch (status) {
      case 'ok':
        return '✓';
      case 'warning':
        return '!';
      case 'error':
        return '✕';
      default:
        return '·';
    }
  }

  protected readonly RouteAdd = RouteAdd;
  protected readonly RouteConnections = RouteConnections;
  protected readonly RouteEdit = RouteEdit;
  protected readonly RoutePlex = RoutePlex;
  protected readonly RouteSettings = RouteSettings;
}
