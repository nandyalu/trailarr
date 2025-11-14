import {Directive, ElementRef, HostListener, inject, Input} from '@angular/core';
import {WebsocketService} from '../services/websocket.service';

@Directive({
  selector: '[appCopyToClipboard]',
})
export class CopyToClipboardDirective {
  @Input('appCopyToClipboard') textToCopy = '';
  webSocketService: WebsocketService;
  element: ElementRef;

  constructor() {
    this.webSocketService = inject(WebsocketService);
    this.element = inject(ElementRef);
    this.element.nativeElement.classList.add('copy');
  }

  @HostListener('click')
  @HostListener('keydown.enter')
  onClick(): void {
    this.copyToClipboard(this.textToCopy);
    console.log('Element with copy button clicked!');
  }

  /**
   * Copies the provided text to the clipboard. If the Clipboard API is not available,
   * it falls back to using the `execCommand` method for wider browser compatibility.
   *
   * @param textToCopy - The text string to be copied to the clipboard.
   * @returns A promise that resolves when the text has been successfully copied.
   *
   * @remarks
   * This method uses the modern Clipboard API if available, and falls back to the
   * `execCommand` method for older browsers. It also displays a toast notification
   * indicating the success or failure of the copy operation.
   *
   * @example
   * ```typescript
   * this.copyToClipboard("Hello, World!");
   * ```
   */
  async copyToClipboard(textToCopy: string) {
    if (!navigator.clipboard) {
      // Fallback to the old execCommand() way (for wider browser coverage)
      const tempInput = document.createElement('input');
      tempInput.value = textToCopy;
      document.body.appendChild(tempInput);
      tempInput.select();
      document.execCommand('copy');
      document.body.removeChild(tempInput);
      this.webSocketService.showToast('Copied to clipboard!');
    } else {
      try {
        await navigator.clipboard.writeText(textToCopy);
        this.webSocketService.showToast('Copied to clipboard!');
      } catch (err) {
        this.webSocketService.showToast('Error copying text to clipboard.', 'Error');
        console.error('Failed to copy: ', err);
      }
    }
    return;
  }
}
