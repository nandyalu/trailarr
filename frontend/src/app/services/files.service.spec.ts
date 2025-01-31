import { TestBed } from '@angular/core/testing';

import { FilesService } from './files.service';

describe('FilesService', () => {
  let service: FilesService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FilesService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
