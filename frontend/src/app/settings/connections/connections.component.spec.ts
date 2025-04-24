import {MockBuilder, MockedComponentFixture, MockRender} from 'ng-mocks';
import {ConnectionsComponent} from './connections.component';

describe('ConnectionsComponent', () => {
  let fixture: MockedComponentFixture<ConnectionsComponent>;

  beforeEach(() => MockBuilder(ConnectionsComponent));

  beforeEach(() => {
    fixture = MockRender(ConnectionsComponent);
    fixture.detectChanges();
  });

  it('has instance', () => expect(fixture.componentInstance).toBeTruthy());

  it('renders', () => expect(fixture).toMatchSnapshot());
});
