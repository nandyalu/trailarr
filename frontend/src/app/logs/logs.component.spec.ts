import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {LogsComponent} from './logs.component';

// Reads the styles Angular injected into the document for this component.
function injectedStyles(): string {
  return Array.from(document.querySelectorAll('style'))
    .map((s) => s.textContent || '')
    .join('\n');
}

describe('LogsComponent', () => {
  let fixture: ComponentFixture<LogsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LogsComponent],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(LogsComponent);
    fixture.detectChanges();
  });

  it('has instance', () => expect(fixture.componentInstance).toBeTruthy());

  // The dropdown anchors to its button through the implicit anchor that
  // popovertarget creates. The button must reference an existing popover.
  it('wires the levelDropdown popover to its button', () => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('button[popovertarget="levelDropdown"]')).not.toBeNull();
    const popover = host.querySelector('#levelDropdown');
    expect(popover).not.toBeNull();
    expect(popover!.getAttribute('popover')).toBe('auto');
    expect(popover!.classList.contains('popover')).toBe(true);
  });

  // Chromium 151+ does not resolve anchor() insets against the implicit
  // anchor, which left popovers at the viewport edge. The styles must anchor
  // popovers with position-area and clear the UA popover inset instead.
  it('anchors popovers with position-area, not anchor() insets', () => {
    const styles = injectedStyles();
    expect(styles).toMatch(/\.popover[^{]*\{[^}]*position-area:\s*block-end span-inline-start/);
    expect(styles).toMatch(/\.popover[^{]*\{[^}]*inset:\s*auto/);
    expect(styles).not.toContain('anchor(');
  });
});
