import {ComponentFixture, TestBed} from '@angular/core/testing';

import {AddCustomFilterDialogComponent} from './add-filter-dialog.component';

describe('AddFilterDialogComponent', () => {
  let component: AddCustomFilterDialogComponent;
  let fixture: ComponentFixture<AddCustomFilterDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddCustomFilterDialogComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(AddCustomFilterDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
