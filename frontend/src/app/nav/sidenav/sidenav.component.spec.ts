import {MockBuilder, MockedComponentFixture, MockRender} from 'ng-mocks';
import {SidenavComponent} from './sidenav.component';

describe('SidenavComponent', () => {
  let fixture: MockedComponentFixture<SidenavComponent>;

  beforeEach(() => MockBuilder(SidenavComponent));

  beforeEach(() => {
    fixture = MockRender(SidenavComponent);
    fixture.detectChanges();
  });

  it('has instance', () => expect(fixture.componentInstance).toBeTruthy());

  it('renders', () => expect(fixture).toMatchSnapshot());
});
