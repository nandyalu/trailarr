import { TestBed } from '@angular/core/testing';

import { MediaService } from './media.service';

describe('Media2Service', () => {
  let service: MediaService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MediaService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
