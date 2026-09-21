/**
 * The known-videos calls of MediaService — Phase 8.
 *
 * These pin the URL shape and the way the YouTube id travels, because the
 * backend reads `yt_id` as a query parameter and a body would be dropped
 * without any error.
 */
import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';
import {provideHttpClient} from '@angular/common/http';
import {TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {MediaVideo} from '../models/media';
import {MediaService} from './media.service';

describe('MediaService known videos', () => {
  let service: MediaService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MediaService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    // Media resources fire their own requests; only assert on ours.
    http.verify({ignoreCancelled: true});
  });

  it('reads the known videos of a media item', () => {
    const videos: Partial<MediaVideo>[] = [{video_id: 'aaa', source: 'tmdb'}];
    let received: MediaVideo[] | undefined;

    service.getMediaVideos(7).subscribe((v) => (received = v));

    const request = http.expectOne('api/v1/media/7/videos');
    expect(request.request.method).toBe('GET');
    request.flush(videos);
    expect(received?.[0].video_id).toBe('aaa');
  });

  it('sends the YouTube id as a query parameter when adding', () => {
    service.addMediaVideo(7, 'https://www.youtube.com/watch?v=abc12345678').subscribe();

    const request = http.expectOne((r) => r.url === 'api/v1/media/7/videos' && r.method === 'POST');
    expect(request.request.params.get('yt_id')).toBe('https://www.youtube.com/watch?v=abc12345678');
    request.flush({});
  });

  it('puts the video id in the path when removing', () => {
    service.deleteMediaVideo(7, 'abc12345678').subscribe();

    const request = http.expectOne('api/v1/media/7/videos/abc12345678');
    expect(request.request.method).toBe('DELETE');
    request.flush({});
  });
});
