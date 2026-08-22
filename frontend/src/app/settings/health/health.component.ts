import {CommonModule} from '@angular/common';
import {ChangeDetectionStrategy, Component, ElementRef, inject, signal, viewChild} from '@angular/core';
import {firstValueFrom} from 'rxjs';
import {ProbeStatus} from 'src/app/models/diagnostics';
import {HealthService} from 'src/app/services/health.service';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';

@Component({
  selector: 'app-health',
  templateUrl: './health.component.html',
  styleUrl: './health.component.scss',
  imports: [CommonModule, LoadIndicatorComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HealthComponent {
  private readonly healthService = inject(HealthService);

  protected readonly report = this.healthService.reportResource;
  protected readonly cookiesStatus = this.healthService.cookiesResource;

  protected readonly running = signal<boolean>(false);
  protected readonly testRunning = signal<boolean>(false);
  protected readonly cookiesBusy = signal<boolean>(false);
  protected readonly message = signal<{type: 'success' | 'error'; text: string} | null>(null);
  protected readonly cookiesText = signal<string>('');
  /** Shown after saving cookies: the next question is always "did that
   * work?", so the answer is one click away instead of a hunt. */
  protected readonly offerCookieTest = signal<boolean>(false);

  private readonly ytdlpConfirmDialog = viewChild.required<ElementRef<HTMLDialogElement>>('ytdlpConfirmDialog');

  protected async runChecks(): Promise<void> {
    if (this.running()) return;
    this.running.set(true);
    this.message.set(null);
    try {
      await firstValueFrom(this.healthService.runChecks());
      this.report.reload();
    } catch (error) {
      this.message.set({type: 'error', text: 'The checks failed to run. ' + (error as Error).message});
    } finally {
      this.running.set(false);
    }
  }

  // yt-dlp live test — behind a confirmation (it contacts YouTube once)
  protected openYtdlpConfirm(): void {
    this.ytdlpConfirmDialog().nativeElement.showModal();
  }

  protected closeYtdlpConfirm(): void {
    this.ytdlpConfirmDialog().nativeElement.close();
  }

  /** Run the test straight from the "Cookies saved" message. The click
   * is the confirmation, so it does not ask twice. */
  protected async testSavedCookies(): Promise<void> {
    this.offerCookieTest.set(false);
    await this.runYtdlpTest();
  }

  protected async runYtdlpTest(): Promise<void> {
    this.closeYtdlpConfirm();
    if (this.testRunning()) return;
    this.testRunning.set(true);
    this.message.set(null);
    try {
      const result = await firstValueFrom(this.healthService.runYtdlpTest(true));
      this.report.reload();
      this.message.set({
        type: result.status === 'ok' ? 'success' : 'error',
        text: result.status === 'ok' ? 'YouTube test passed. ' + result.detail : 'YouTube test failed. ' + result.detail,
      });
    } catch (error) {
      this.message.set({type: 'error', text: 'The YouTube test failed to run. ' + (error as Error).message});
    } finally {
      this.testRunning.set(false);
    }
  }

  protected onCookiesFile(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => this.cookiesText.set(String(reader.result ?? ''));
    reader.readAsText(file);
    input.value = '';
  }

  protected async saveCookies(): Promise<void> {
    const content = this.cookiesText();
    if (!content.trim() || this.cookiesBusy()) return;
    this.cookiesBusy.set(true);
    this.message.set(null);
    try {
      await firstValueFrom(this.healthService.uploadCookies(content));
      this.cookiesText.set('');
      this.cookiesResourcesReload();
      this.message.set({type: 'success', text: 'Cookies saved. yt-dlp uses them on the next download.'});
      this.offerCookieTest.set(true);
    } catch (error) {
      const detail = (error as {error?: {detail?: string}})?.error?.detail ?? (error as Error).message;
      this.message.set({type: 'error', text: 'Could not save the cookies. ' + detail});
    } finally {
      this.cookiesBusy.set(false);
    }
  }

  protected async deleteCookies(): Promise<void> {
    if (this.cookiesBusy()) return;
    this.cookiesBusy.set(true);
    this.message.set(null);
    try {
      await firstValueFrom(this.healthService.deleteCookies());
      this.cookiesResourcesReload();
      this.offerCookieTest.set(false);
      this.message.set({type: 'success', text: 'Cookies removed.'});
    } catch (error) {
      this.message.set({type: 'error', text: 'Could not remove the cookies. ' + (error as Error).message});
    } finally {
      this.cookiesBusy.set(false);
    }
  }

  private cookiesResourcesReload(): void {
    this.cookiesStatus.reload();
    this.report.reload();
  }

  protected statusIcon(status: ProbeStatus): string {
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
}
