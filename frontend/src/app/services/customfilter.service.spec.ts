import {TestBed} from '@angular/core/testing';

import {CustomfilterService} from './customfilter.service';

describe('CustomfilterService', () => {
  let service: CustomfilterService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(CustomfilterService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
