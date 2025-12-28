import {HttpClient} from '@angular/common/http';
import {TestBed} from '@angular/core/testing';
import {firstValueFrom, of} from 'rxjs';
import {vi} from 'vitest';
import {LogsService} from './logs.service';

describe('LogsService', () => {
  let instance: LogsService;
  let httpClientMock: {get: ReturnType<typeof vi.fn>};

  beforeEach(async () => {
    httpClientMock = {get: vi.fn(() => of('meh'))};

    await TestBed.configureTestingModule({
      providers: [{provide: HttpClient, useValue: httpClientMock}],
    }).compileComponents();

    instance = TestBed.inject(LogsService);
  });

  it(`creates instance`, () => expect(instance).toBeTruthy());

  it(`downloads logs`, async () => {
    const ret = await firstValueFrom(instance.downloadLogs());
    expect(ret).toBe('meh');
    expect(httpClientMock.get).toHaveBeenCalledWith('/api/v1/logs/download', {responseType: 'blob'});
  });

  it(`gets logs`, async () => {
    const ret = await firstValueFrom(instance.getLogs());
    expect(ret).toBe('meh');
    expect(httpClientMock.get).toHaveBeenCalledWith('/api/v1/logs/');
  });
});
