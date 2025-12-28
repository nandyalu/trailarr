import { DisplayTitlePipe } from './display-title.pipe';

describe('DisplayTitlePipe', () => {
  it('create an instance', () => {
    const pipe = new DisplayTitlePipe();
    expect(pipe).toBeTruthy();
  });

  describe('DisplayTitlePipe', () => {
    it('create an instance', () => {
      const pipe = new DisplayTitlePipe();
      expect(pipe).toBeTruthy();
    });

    describe('transform', () => {
      let pipe: DisplayTitlePipe;

      beforeEach(() => {
        pipe = new DisplayTitlePipe();
      });

      it('should convert lowercase to title case', () => {
        expect(pipe.transform('hello world')).toBe('Hello World');
      });

      it('should convert underscores to spaces', () => {
        expect(pipe.transform('hello_world')).toBe('Hello World');
      });

      it('should handle multiple underscores', () => {
        expect(pipe.transform('hello___world')).toBe('Hello World');
      });

      it('should collapse multiple spaces into single space', () => {
        expect(pipe.transform('hello   world')).toBe('Hello World');
      });

      it('should trim leading and trailing whitespace', () => {
        expect(pipe.transform('  hello world  ')).toBe('Hello World');
      });

      it('should handle mixed underscores and spaces', () => {
        expect(pipe.transform('hello_  _world')).toBe('Hello World');
      });

      it('should capitalize first letter of each word', () => {
        expect(pipe.transform('the quick brown fox')).toBe('The Quick Brown Fox');
      });

      it('should handle uppercase input', () => {
        expect(pipe.transform('HELLO WORLD')).toBe('Hello World');
      });

      it('should handle mixed case input', () => {
        expect(pipe.transform('HeLLo WoRLd')).toBe('Hello World');
      });

      it('should handle single word', () => {
        expect(pipe.transform('hello')).toBe('Hello');
      });

      it('should handle empty string', () => {
        expect(pipe.transform('')).toBe('');
      });

      it('should handle string with only spaces', () => {
        expect(pipe.transform('   ')).toBe('');
      });

      it('should handle string with only underscores', () => {
        expect(pipe.transform('___')).toBe('');
      });

      it('should handle complex cases with numbers', () => {
        expect(pipe.transform('hello_world_123')).toBe('Hello World 123');
      });
    });
  });


});
