import {Component} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {CopyToClipboardDirective} from './copy-to-clipboard.directive';

@Component({
  template: `<button appCopyToClipboard [textToCopy]="'test text'">Copy</button>`,
  imports: [CopyToClipboardDirective],
})
class TestHostComponent {}

describe('CopyToClipboardDirective', () => {
  let fixture: ComponentFixture<TestHostComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TestHostComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TestHostComponent);
    fixture.detectChanges();
  });

  it('should create an instance', () => {
    const button = fixture.nativeElement.querySelector('button');
    expect(button).toBeTruthy();
    expect(button.classList.contains('copy')).toBe(true);
  });
});
