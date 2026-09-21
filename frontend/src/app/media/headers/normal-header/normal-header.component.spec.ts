import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {NormalHeaderComponent} from './normal-header.component';

// Reads the styles Angular injected into the document for this component.
function injectedStyles(): string {
  return Array.from(document.querySelectorAll('style'))
    .map((s) => s.textContent || '')
    .join('\n');
}

describe('NormalHeaderComponent', () => {
  let fixture: ComponentFixture<NormalHeaderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NormalHeaderComponent],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(NormalHeaderComponent);
    fixture.detectChanges();
  });

  it('has instance', () => expect(fixture.componentInstance).toBeTruthy());

  // The dropdowns anchor to their buttons through the implicit anchor that
  // popovertarget creates. Each button must reference an existing popover.
  it.each(['viewDropdown', 'sortDropdown', 'filterDropdown'])('wires the %s popover to its button', (id) => {
    const host: HTMLElement = fixture.nativeElement;
    const button = host.querySelector(`button[popovertarget="${id}"]`);
    expect(button).not.toBeNull();
    const popover = host.querySelector(`#${id}`);
    expect(popover).not.toBeNull();
    expect(popover!.getAttribute('popover')).toBe('auto');
    expect(popover!.classList.contains('popover')).toBe(true);
  });

  // #618: the filter button carries "matched / total" for the current view.
  it('renders the filter count on the filter button', () => {
    const host: HTMLElement = fixture.nativeElement;
    const button = host.querySelector('button[popovertarget="filterDropdown"]')!;
    const count = button.querySelector('.filter-count');
    expect(count).not.toBeNull();
    expect(count!.textContent!.trim()).toMatch(/^\d+ \/ \d+$/);
    // An aria-label would otherwise reduce the button to just "Filter".
    expect(button.getAttribute('aria-label')).toMatch(/showing \d+ of \d+/);
  });

  // The header collapses to icons on a phone. The count stays, but only while
  // there is room beside the icons — the rule must have a lower bound, or a
  // 320px phone shows the count jammed against the Edit button.
  it('shows the filter count on a phone only above the narrow-screen bound', () => {
    const styles = injectedStyles();
    const rule = /@media[^{]*360px[^{]*\{\s*[^{}]*\.filter-count[^{]*\{[^}]*display:\s*inline/;
    expect(styles).toMatch(rule);
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
