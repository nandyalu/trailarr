import {RemoveStartingSlashPipe} from './remove-starting-slash.pipe';

describe('RemoveStartingSlashPipe', () => {
  it('create an instance', () => {
    const pipe = new RemoveStartingSlashPipe();
    expect(pipe).toBeTruthy();
  });

  it('should remove starting slash', () => {
    const pipe = new RemoveStartingSlashPipe();
    expect(pipe.transform('/test')).toBe('test');
  });

  it('should not change string without starting slash', () => {
    const pipe = new RemoveStartingSlashPipe();
    expect(pipe.transform('test')).toBe('test');
  });

  it('should handle null', () => {
    const pipe = new RemoveStartingSlashPipe();
    expect(pipe.transform(null)).toBeNull();
  });

  it('should handle undefined', () => {
    const pipe = new RemoveStartingSlashPipe();
    expect(pipe.transform(undefined)).toBeUndefined();
  });
});
