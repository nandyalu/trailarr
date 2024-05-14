import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ShowConnectionsComponent } from './show-connections.component';

describe('ShowConnectionsComponent', () => {
  let component: ShowConnectionsComponent;
  let fixture: ComponentFixture<ShowConnectionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ShowConnectionsComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ShowConnectionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
