import {MockBuilder, MockedComponentFixture, MockRender} from 'ng-mocks';
import {SettingsComponent} from './settings.component';

describe('SettingsComponent', () => {
  let fixture: MockedComponentFixture<SettingsComponent>;

  beforeEach(() => MockBuilder(SettingsComponent));

  beforeEach(() => {
    fixture = MockRender(SettingsComponent);
    fixture.detectChanges();
  });

  it('has instance', () => expect(fixture.componentInstance).toBeTruthy());

  it('renders', () => expect(fixture).toMatchSnapshot());
});
