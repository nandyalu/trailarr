import {TestBed} from '@angular/core/testing';
import {DurationConvertPipe} from './duration-pipe';

describe(`DurationConvertPipe`, () => {
  let instance: DurationConvertPipe;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      providers: [DurationConvertPipe],
    }).compileComponents();

    instance = TestBed.inject(DurationConvertPipe);
  });

  it(`creates instance`, () => expect(instance).toBeTruthy());

  it(`transforms`, () => expect(instance.transform(62)).toBe('1h 2m'));
});
