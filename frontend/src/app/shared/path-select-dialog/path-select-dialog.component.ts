import {ChangeDetectionStrategy, Component, effect, ElementRef, inject, input, model, output, signal, viewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {SettingsService} from 'src/app/services/settings.service';
import {LoadIndicatorComponent} from '../load-indicator';

@Component({
  selector: 'app-path-select-dialog',
  imports: [FormsModule, LoadIndicatorComponent],
  templateUrl: './path-select-dialog.component.html',
  styleUrl: './path-select-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PathSelectDialogComponent {
  protected readonly settingsService = inject(SettingsService);

  name = input.required<string>();
  path = model.required<string>();
  pathShouldEndWith = input.required<string>();
  isSubmitted = signal(false);

  isLoading = this.settingsService.filesResource.isLoading;
  folders = this.settingsService.filesResource.value;

  oldPath = signal<string>('');
  onSubmit = output<string>();

  constructor() {
    effect(() => {
      const _path = this.path();
      if (!_path) {
        this.settingsService.filesPath.set('/');
      }
      if (_path.endsWith('/')) {
        this.settingsService.filesPath.set(_path);
      }
    });
  }

  ngOnChanges() {
    this.oldPath.set(this.path());
  }

  ngAfterViewInit() {
    this.showDialog();
  }

  readonly pathSelectDialog = viewChild.required<ElementRef<HTMLDialogElement>>('pathSelectDialog');
  protected showDialog = () => this.pathSelectDialog().nativeElement.showModal();
  protected closeDialog = () => this.pathSelectDialog().nativeElement.close();

  setPath(path1: string, type: string = 'folder') {
    if (!path1.endsWith('/') && type === 'folder') {
      path1 += '/';
    }
    this.path.set(path1);
  }

  goUpOneLevel() {
    let path1 = this.path();
    if (path1.endsWith('/')) {
      path1 = path1.slice(0, -1); // Remove the trailing slash
    }
    path1 = path1.replace(/\/[^\/]*$/, ''); // Remove the last segment
    this.setPath(path1);
  }

  resetValue(): void {
    this.path.set(this.oldPath());
  }

  cancelDialog(): void {
    this.path.set(this.oldPath());
    this.onSubmit.emit('');
    this.closeDialog();
  }

  submitValue(): void {
    this.isSubmitted.set(true);
    let submitValue = this.path();
    submitValue = submitValue.toString().trim();
    this.onSubmit.emit(submitValue);
    this.oldPath.set(submitValue);
  }
}
