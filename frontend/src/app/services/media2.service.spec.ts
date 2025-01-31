import { TestBed } from '@angular/core/testing';

import { Media2Service } from './media2.service';

describe('Media2Service', () => {
  let service: Media2Service;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Media2Service);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
