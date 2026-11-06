/**
 * The banner about unmonitored items that the TMDB upgrade skips (#707).
 *
 * Before v0.10.0, Trailarr turned monitoring off after each download, so
 * an old library has many such items. The banner lists them until the user
 * monitors them or closes it. A closed banner stays closed in this browser,
 * and Trailarr stops asking the backend for the list.
 */
import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';
import {provideHttpClient} from '@angular/common/http';
import {TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {mapUnmonitoredUpgrades} from '../models/pending';
import {MediaService, UNMONITORED_UPGRADES_DISMISSED_KEY} from './media.service';

const URL = 'api/v1/media/unmonitored_upgrades';

describe('MediaService unmonitored upgrades', () => {
  let http: HttpTestingController;

  function setup(): MediaService {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
    return TestBed.inject(MediaService);
  }

  beforeEach(() => localStorage.removeItem(UNMONITORED_UPGRADES_DISMISSED_KEY));
  afterEach(() => localStorage.removeItem(UNMONITORED_UPGRADES_DISMISSED_KEY));

  it('reads the list until the banner is closed, and remembers that it is closed', async () => {
    const service = setup();
    TestBed.tick();
    http.expectOne(URL).flush({media_ids: [4, 9], other_downloads: 1});
    // The resource sets its value after the response, not during it.
    await new Promise((resolve) => setTimeout(resolve, 0));
    TestBed.tick();
    expect(service.unmonitoredUpgradesResource.value()).toEqual({media_ids: [4, 9], other_downloads: 1});

    service.dismissUnmonitoredUpgrades();
    TestBed.tick();

    expect(service.unmonitoredUpgradesDismissed()).toBe(true);
    expect(localStorage.getItem(UNMONITORED_UPGRADES_DISMISSED_KEY)).toBe('true');
    expect(http.match(URL)).toHaveLength(0);
  });

  it('does not ask the backend once the banner was closed in this browser', () => {
    localStorage.setItem(UNMONITORED_UPGRADES_DISMISSED_KEY, 'true');
    const service = setup();
    TestBed.tick();

    expect(service.unmonitoredUpgradesDismissed()).toBe(true);
    expect(http.match(URL)).toHaveLength(0);
  });
});

describe('mapUnmonitoredUpgrades', () => {
  it('reads an empty or broken answer as no items', () => {
    expect(mapUnmonitoredUpgrades(null)).toEqual({media_ids: [], other_downloads: 0});
    expect(mapUnmonitoredUpgrades({media_ids: 'x'})).toEqual({media_ids: [], other_downloads: 0});
    expect(mapUnmonitoredUpgrades({media_ids: [1], other_downloads: 2})).toEqual({media_ids: [1], other_downloads: 2});
  });
});
