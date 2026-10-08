/**
 * The Known videos list on media details — Phase 8, extended in Phase 9.
 *
 * The list is the visible half of the resolver: it must show the videos in
 * the order Trailarr would try them, name the source of each, and mark the
 * one the user chose, because that is the row automation never touches.
 * Phase 9 groups the list by type (Trailer first), makes it the picker for
 * a per-row download, and makes the Watch button open the first video,
 * because `media.youtube_trailer_id` is gone (H9).
 */
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {Observable, of} from 'rxjs';
import {MediaVideo} from 'src/app/models/media';
import {TrailerProfileRead} from 'src/app/models/trailerprofile';
import {MediaService} from 'src/app/services/media.service';
import {ProfileService} from 'src/app/services/profile.service';
import {groupVideosByType, MediaDetailsComponent, normalizeVideoType} from './media-details.component';

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

function profile(id: number, name: string, videoType?: string): TrailerProfileRead {
  return {
    id,
    customfilter_id: id,
    customfilter: {id, filter_name: name, filter_type: 'TRAILER', filters: []},
    video_type: videoType,
  } as unknown as TrailerProfileRead;
}

describe('groupVideosByType', () => {
  it('puts trailers first, then the other types in enum order, keeping the server order inside a group', () => {
    // TMDB lists featurettes before trailers for some titles.
    const videos = [
      video({id: 1, video_id: 'feat-1', video_type: 'featurette'}),
      video({id: 2, video_id: 'teaser-1', video_type: 'teaser'}),
      video({id: 3, video_id: 'trailer-2', video_type: 'trailer', source: 'arr'}),
      video({id: 4, video_id: 'feat-2', video_type: 'featurette'}),
      video({id: 5, video_id: 'trailer-1', video_type: 'trailer', source: 'user'}),
    ];

    const groups = groupVideosByType(videos);

    expect(groups.map((g) => g.type)).toEqual(['trailer', 'teaser', 'featurette']);
    expect(groups.map((g) => g.label)).toEqual(['Trailer', 'Teaser', 'Featurette']);
    expect(groups[0].videos.map((v) => v.video_id)).toEqual(['trailer-2', 'trailer-1']);
    expect(groups[2].videos.map((v) => v.video_id)).toEqual(['feat-1', 'feat-2']);
  });

  it('reads an empty or unknown type as a trailer', () => {
    expect(normalizeVideoType('')).toBe('trailer');
    expect(normalizeVideoType(undefined)).toBe('trailer');
    expect(normalizeVideoType('Featurette')).toBe('featurette');
    expect(normalizeVideoType('made-up')).toBe('trailer');
    expect(groupVideosByType([video({video_type: ''})])[0].type).toBe('trailer');
  });

  it('is empty for no videos', () => {
    expect(groupVideosByType([])).toEqual([]);
  });
});

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

  it('names each type', () => {
    expect(component.typeLabel('behind_the_scenes')).toBe('Behind the Scenes');
    expect(component.typeLabel(undefined)).toBe('Trailer');
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
    // The Watch button opens the first trailer: the video a download takes.
    expect(component.firstVideo()?.video_id).toBe('mine');
    expect(component.watchTitle()).toBe('Opens the first known trailer on YouTube');
  });

  it('opens the first trailer on Watch, not a featurette or a user row of another type that comes first', () => {
    // TMDB sequences restart for each type, and a USER row of any type
    // comes first in the list, so the first row is not always a trailer.
    const videos = [
      video({id: 1, video_id: 'my-feature1', source: 'user', video_type: 'featurette'}),
      video({id: 2, video_id: 'bts00000000', source: 'tmdb', video_type: 'behind_the_scenes', sequence: 0}),
      video({id: 3, video_id: 'trailer2222', source: 'tmdb', video_type: 'trailer', sequence: 0}),
      video({id: 4, video_id: 'trailer1111', source: 'tmdb', video_type: 'trailer', sequence: 1}),
    ];
    const service = TestBed.inject(MediaService);
    vi.spyOn(service, 'getMediaVideos').mockReturnValue(of(videos));
    vi.spyOn(component, 'mediaId').mockReturnValue(7 as never);
    const open = vi.spyOn(window, 'open').mockImplementation(() => null);

    component.loadKnownVideos();
    component.openTrailer();

    expect(component.firstVideo()?.video_id).toBe('trailer2222');
    expect(open).toHaveBeenCalledWith('https://www.youtube.com/watch?v=trailer2222', '_blank');
    open.mockRestore();
  });

  it('falls back to the first video of any type when no trailer is known, and says so', () => {
    const videos = [
      video({id: 1, video_id: 'feat0000000', source: 'tmdb', video_type: 'featurette'}),
      video({id: 2, video_id: 'clip0000000', source: 'tmdb', video_type: 'clip'}),
    ];
    const service = TestBed.inject(MediaService);
    vi.spyOn(service, 'getMediaVideos').mockReturnValue(of(videos));
    vi.spyOn(component, 'mediaId').mockReturnValue(7 as never);

    component.loadKnownVideos();

    expect(component.firstVideo()?.video_id).toBe('feat0000000');
    expect(component.watchTitle()).toBe('Trailarr knows no trailer for this item. Opens the first known featurette on YouTube');
  });

  it('reads a video with no type as a trailer for Watch', () => {
    const videos = [
      video({id: 1, video_id: 'feat0000000', video_type: 'featurette'}),
      video({id: 2, video_id: 'untyped0000', video_type: ''}),
    ];
    const service = TestBed.inject(MediaService);
    vi.spyOn(service, 'getMediaVideos').mockReturnValue(of(videos));
    vi.spyOn(component, 'mediaId').mockReturnValue(7 as never);

    component.loadKnownVideos();

    expect(component.firstVideo()?.video_id).toBe('untyped0000');
  });

  it('has nothing to watch when the list is empty', () => {
    const service = TestBed.inject(MediaService);
    vi.spyOn(service, 'getMediaVideos').mockReturnValue(of([]));
    vi.spyOn(component, 'mediaId').mockReturnValue(7 as never);
    const open = vi.spyOn(window, 'open').mockImplementation(() => null);

    component.loadKnownVideos();
    component.openTrailer();

    expect(component.firstVideo()).toBeNull();
    expect(component.watchTitle()).toBe('Trailarr knows no video for this item');
    expect(open).not.toHaveBeenCalled();
  });

  it('opens the first known video on Watch', () => {
    const service = TestBed.inject(MediaService);
    vi.spyOn(service, 'getMediaVideos').mockReturnValue(of([video({video_id: 'first000000'})]));
    vi.spyOn(component, 'mediaId').mockReturnValue(7 as never);
    const open = vi.spyOn(window, 'open').mockImplementation(() => null);

    component.loadKnownVideos();
    component.openTrailer();

    expect(open).toHaveBeenCalledWith('https://www.youtube.com/watch?v=first000000', '_blank');
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

  it('offers only the profiles of the row type for a per-row download, reading a missing type as trailer', () => {
    const profiles = TestBed.inject(ProfileService);
    vi.spyOn(profiles.allProfiles, 'value').mockReturnValue([
      profile(1, 'HD Trailers'),
      profile(2, 'Featurettes', 'featurette'),
      profile(3, '4K Trailers', 'trailer'),
    ]);

    expect(component.profilesForType('trailer').map((p) => p.id)).toEqual([1, 3]);
    expect(component.profilesForType('featurette').map((p) => p.id)).toEqual([2]);
    expect(component.profilesForType('bloopers')).toEqual([]);
  });

  it('downloads a known video with the chosen profile and its id', () => {
    const service = TestBed.inject(MediaService);
    const download = vi.spyOn(service, 'downloadMediaTrailer').mockReturnValue(of('started'));
    vi.spyOn(component, 'mediaId').mockReturnValue(7 as never);
    const popover = {hidePopover: vi.fn()} as unknown as HTMLElement;

    component.downloadKnownVideo(video({video_id: 'chosen00000'}), 2, popover);

    expect(popover.hidePopover).toHaveBeenCalled();
    expect(download).toHaveBeenCalledWith(7, 2, 'chosen00000');
  });

  it('adds a video with its language and type, then clears the form', () => {
    const service = TestBed.inject(MediaService);
    const add = vi.spyOn(service, 'addMediaVideo').mockReturnValue(of(video({video_id: 'new00000000'})));
    vi.spyOn(service, 'getMediaVideos').mockReturnValue(of([]));
    vi.spyOn(component, 'mediaId').mockReturnValue(7 as never);
    component.newVideoUrl = ' https://youtu.be/new00000000 ';
    component.videoLanguage = 'it';
    component.newVideoType = 'featurette';

    component.addChosenVideo();

    expect(add).toHaveBeenCalledWith(7, 'https://youtu.be/new00000000', 'it', 'featurette');
    expect(component.newVideoUrl).toBe('');
    expect(component.videoLanguage).toBe('');
    expect(component.newVideoType).toBe('trailer');
  });

  it('does not call the server for an empty add form', () => {
    const service = TestBed.inject(MediaService);
    const add = vi.spyOn(service, 'addMediaVideo');
    component.newVideoUrl = '   ';

    component.addChosenVideo();

    expect(add).not.toHaveBeenCalled();
  });
});
