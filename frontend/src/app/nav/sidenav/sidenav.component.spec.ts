import {Router} from '@angular/router';
import {MockBuilder, MockedComponentFixture, MockRender} from 'ng-mocks';
import {of} from 'rxjs';
import {SidenavComponent} from './sidenav.component';

class MockRouter {
  events = of();
}

describe('SidenavComponent', () => {
  let fixture: MockedComponentFixture<SidenavComponent>;

  beforeEach(() => MockBuilder(SidenavComponent).mock(Router, new MockRouter()));

  beforeEach(() => {
    fixture = MockRender(SidenavComponent);
    fixture.detectChanges();
  });

  it('has instance', () => expect(fixture.componentInstance).toBeTruthy());

  it('renders', () => expect(fixture).toMatchSnapshot());
});
