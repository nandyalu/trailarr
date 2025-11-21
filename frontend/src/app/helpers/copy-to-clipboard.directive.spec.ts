import { ElementRef } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { WebsocketService } from '../services/websocket.service';
import { CopyToClipboardDirective } from './copy-to-clipboard.directive';

class MockElementRef extends ElementRef {
  constructor() {
    super(document.createElement('div'));
  }
}

class MockWebsocketService {}

describe('CopyToClipboardDirective', () => {
  it('should create an instance', () => {
    TestBed.configureTestingModule({
      providers: [
        CopyToClipboardDirective,
        { provide: ElementRef, useClass: MockElementRef },
        { provide: WebsocketService, useClass: MockWebsocketService },
      ],
    });
    const directive = TestBed.inject(CopyToClipboardDirective);
    expect(directive).toBeTruthy();
  });
});
