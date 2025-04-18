import {ComponentFixture, TestBed} from '@angular/core/testing';

import {EditConnectionComponent} from './edit-connection.component';

describe('EditConnectionComponent', () => {
  let component: EditConnectionComponent;
  let fixture: ComponentFixture<EditConnectionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EditConnectionComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(EditConnectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
