import {HttpClient} from '@angular/common/http';
import {TestBed} from '@angular/core/testing';
import {MockBuilder, ngMocks} from 'ng-mocks';
import {firstValueFrom, of} from 'rxjs';
import {LogsService} from './logs.service';

describe('LogsService', () => {
  let instance: LogsService;

  beforeEach(() => MockBuilder(LogsService).provide({provide: HttpClient, useValue: {get: jest.fn(() => of('meh'))}}));

  beforeEach(() => {
    instance = TestBed.inject(LogsService);
  });

  it(`creates instance`, () => expect(instance).toBeTruthy());

  it(`downloads logs`, async () => {
    const ret = await firstValueFrom(instance.downloadLogs());
    expect(ret).toBe('meh');
    expect(ngMocks.findInstance(HttpClient).get).toHaveBeenCalledWith('/api/v1/logs/download', {responseType: 'blob'});
  });

  it(`gets logs`, async () => {
    const ret = await firstValueFrom(instance.getLogs());
    expect(ret).toBe('meh');
    expect(ngMocks.findInstance(HttpClient).get).toHaveBeenCalledWith('/api/v1/logs/');
  });
});
