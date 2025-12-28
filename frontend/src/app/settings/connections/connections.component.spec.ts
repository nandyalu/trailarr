import {ComponentFixture, TestBed} from '@angular/core/testing';
import {ConnectionsComponent} from './connections.component';

describe('ConnectionsComponent', () => {
  let fixture: ComponentFixture<ConnectionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConnectionsComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ConnectionsComponent);
    fixture.detectChanges();
  });

  it('has instance', () => expect(fixture.componentInstance).toBeTruthy());

  it('renders', () => expect(fixture.nativeElement).toMatchSnapshot());
});
