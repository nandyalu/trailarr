import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {EventsComponent} from './events.component';

// Reads the styles Angular injected into the document for this component.
function injectedStyles(): string {
  return Array.from(document.querySelectorAll('style'))
    .map((s) => s.textContent || '')
    .join('\n');
}

describe('EventsComponent', () => {
  let fixture: ComponentFixture<EventsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EventsComponent],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(EventsComponent);
    fixture.detectChanges();
  });

  it('has instance', () => expect(fixture.componentInstance).toBeTruthy());

  // The dropdowns anchor to their buttons through the implicit anchor that
  // popovertarget creates. Each button must reference an existing popover.
  it.each(['sourceDropdown', 'typeDropdown'])('wires the %s popover to its button', (id) => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector(`button[popovertarget="${id}"]`)).not.toBeNull();
    const popover = host.querySelector(`#${id}`);
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
