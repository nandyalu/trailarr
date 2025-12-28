import {ComponentFixture, TestBed} from '@angular/core/testing';
import {LoadIndicatorComponent} from './load-indicator.component';

describe('LoadIndicatorComponent', () => {
  let fixture: ComponentFixture<LoadIndicatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoadIndicatorComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(LoadIndicatorComponent);
    fixture.detectChanges();
  });

  it('has instance', () => expect(fixture.componentInstance).toBeTruthy());

  it('renders', () => expect(fixture.nativeElement).toMatchSnapshot());
});
