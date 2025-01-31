import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FilesComponent } from './files.component';

describe('FilesComponent', () => {
  let component: FilesComponent;
  let fixture: ComponentFixture<FilesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FilesComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FilesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
