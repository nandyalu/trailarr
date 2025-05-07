import {MockBuilder, MockedComponentFixture, MockRender} from 'ng-mocks';
import {LoadIndicatorComponent} from './load-indicator.component';

describe('LoadIndicatorComponent', () => {
  let fixture: MockedComponentFixture<LoadIndicatorComponent>;

  beforeEach(() => MockBuilder(LoadIndicatorComponent));

  beforeEach(() => {
    fixture = MockRender(LoadIndicatorComponent);
    fixture.detectChanges();
  });

  it('has instance', () => expect(fixture.componentInstance).toBeTruthy());

  it('renders', () => expect(fixture).toMatchSnapshot());
});
