/**
 * The Known videos list on media details — Phase 8.
 *
 * The list is the visible half of the resolver: it must show the videos in
 * the order Trailarr would try them, name the source of each, and mark the
 * one the user chose, because that is the row automation never touches.
 */
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {Observable, of} from 'rxjs';
import {MediaVideo} from 'src/app/models/media';
import {MediaService} from 'src/app/services/media.service';
import {MediaDetailsComponent} from './media-details.component';

function video(partial: Partial<MediaVideo>): MediaVideo {
  return {
    id: 1,
    media_id: 7,
    video_id: 'aaa',
    source: 'tmdb',
    season: null,
    video_type: 'trailer',
    sequence: 0,
    language: 'en',
    name: '',
    official: true,
    published_at: null,
    added_at: '',
    updated_at: '',
    ...partial,
  };
}

describe('MediaDetailsComponent known videos', () => {
  let fixture: ComponentFixture<MediaDetailsComponent>;
  let component: MediaDetailsComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MediaDetailsComponent],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(MediaDetailsComponent);
    component = fixture.componentInstance;
  });

  it('names each source in words a user can read', () => {
    expect(component.sourceLabel('user')).toBe('You chose this');
    expect(component.sourceLabel('tmdb')).toBe('TMDB');
    expect(component.sourceLabel('arr')).toBe('Radarr / Sonarr');
    expect(component.sourceLabel('search')).toBe('YouTube search');
  });

  it('links a video to YouTube', () => {
    expect(component.youtubeLink('abc12345678')).toBe('https://www.youtube.com/watch?v=abc12345678');
  });

  it('keeps the order the server sent', () => {
    // The server sorts by source and language; the page must not re-sort.
    const videos = [
      video({id: 1, video_id: 'mine', source: 'user'}),
      video({id: 2, video_id: 'curated', source: 'tmdb'}),
      video({id: 3, video_id: 'from-arr', source: 'arr'}),
    ];
    const service = TestBed.inject(MediaService);
    vi.spyOn(service, 'getMediaVideos').mockReturnValue(of(videos));
    vi.spyOn(component, 'mediaId').mockReturnValue(7 as never);

    component.loadKnownVideos();

    expect(component.knownVideos().map((v) => v.video_id)).toEqual(['mine', 'curated', 'from-arr']);
  });

  it('shows an empty list when the request fails', () => {
    // The list is extra information: a failure must not take over the page.
    const service = TestBed.inject(MediaService);
    vi.spyOn(service, 'getMediaVideos').mockReturnValue(
      new Observable((subscriber) => subscriber.error(new Error('boom'))),
    );
    vi.spyOn(component, 'mediaId').mockReturnValue(7 as never);

    component.loadKnownVideos();

    expect(component.knownVideos()).toEqual([]);
  });
});
