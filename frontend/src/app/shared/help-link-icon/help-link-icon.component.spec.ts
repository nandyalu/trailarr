import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HelpLinkIconComponent } from './help-link-icon.component';

describe('HelpLinkIconComponent', () => {
  let component: HelpLinkIconComponent;
  let fixture: ComponentFixture<HelpLinkIconComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HelpLinkIconComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HelpLinkIconComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
