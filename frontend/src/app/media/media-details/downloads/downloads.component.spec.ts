import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {Download} from 'src/app/models/media';
import {DownloadsComponent} from './downloads.component';

const fakeDownload: Download = {
  id: 42,
  path: '/media/movie/trailer.mkv',
  file_name: 'trailer.mkv',
  file_hash: 'abc123',
  size: 12345678,
  resolution: 1080,
  file_format: 'mkv',
  video_format: 'h264',
  audio_format: 'aac',
  audio_language: 'eng',
  subtitle_format: null,
  subtitle_language: null,
  duration: 120,
  youtube_id: 'dQw4w9WgXcQ',
  youtube_channel: 'Trailers',
  file_exists: true,
  profile_id: 0,
  media_id: 7,
  added_at: new Date('2026-01-01T00:00:00Z'),
  updated_at: new Date('2026-01-01T00:00:00Z'),
};

// Reads the styles Angular injected into the document for this component.
function injectedStyles(): string {
  return Array.from(document.querySelectorAll('style'))
    .map((s) => s.textContent || '')
    .join('\n');
}

describe('DownloadsComponent', () => {
  let fixture: ComponentFixture<DownloadsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DownloadsComponent],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(DownloadsComponent);
    fixture.componentRef.setInput('downloads', [fakeDownload]);
    fixture.detectChanges();
  });

  it('has instance', () => expect(fixture.componentInstance).toBeTruthy());

  // A download with no profile shows an assign button. The popover anchors to
  // it through the implicit anchor that popovertarget creates, so the button
  // must reference an existing popover.
  it('wires the assign-profile popover to its button', () => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('button[popovertarget="assignProfilePopover42"]')).not.toBeNull();
    const popover = host.querySelector('#assignProfilePopover42');
    expect(popover).not.toBeNull();
    expect(popover!.getAttribute('popover')).toBe('auto');
    expect(popover!.classList.contains('popover')).toBe(true);
  });

  // Chromium 151+ does not resolve anchor() insets against the implicit
  // anchor, which left popovers at the viewport edge. The styles must anchor
  // popovers with position-area and clear the UA popover inset instead.
  it('anchors popovers with position-area, not anchor() insets', () => {
    const styles = injectedStyles();
    expect(styles).toMatch(/\.popover[^{]*\{[^}]*position-area:\s*block-end span-inline-end/);
    expect(styles).toMatch(/\.popover[^{]*\{[^}]*inset:\s*auto/);
    expect(styles).toMatch(/\.open-up[^{]*\{[^}]*position-area:\s*block-start span-inline-end/);
    expect(styles).not.toContain('anchor(');
  });
});
