import {APP_BASE_HREF} from '@angular/common';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {of} from 'rxjs';
import {vi} from 'vitest';
import {AuthService} from '../../services/auth.service';
import {LoginComponent} from './login.component';

// The app is also served below a URL base (reverse proxy setup). A redirect to
// an absolute path after login removes that base, the app then loads from the
// server root, and the session cookie no longer matches the requests.
// See https://github.com/nandyalu/trailarr/issues/663
describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let locationStub: {search: string; href: string};
  let originalLocation: PropertyDescriptor;

  async function setupWith(baseHref: string, search: string) {
    locationStub = {search, href: ''};
    originalLocation = Object.getOwnPropertyDescriptor(window, 'location')!;
    Object.defineProperty(window, 'location', {configurable: true, writable: true, value: locationStub});

    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        provideRouter([]),
        {provide: APP_BASE_HREF, useValue: baseHref},
        {
          provide: AuthService,
          useValue: {
            checkAuthStatus: vi.fn(() => of(false)),
            login: vi.fn(() => of(undefined)),
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();
  }

  function signIn() {
    const host: HTMLElement = fixture.nativeElement;
    const username = host.querySelector('#username') as HTMLInputElement;
    const password = host.querySelector('#password') as HTMLInputElement;
    username.value = 'admin';
    username.dispatchEvent(new Event('input'));
    password.value = 'trailarr';
    password.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    host.querySelector('form')!.dispatchEvent(new Event('submit', {cancelable: true}));
  }

  afterEach(() => {
    Object.defineProperty(window, 'location', originalLocation);
    TestBed.resetTestingModule();
  });

  it('keeps the URL base in the redirect after login', async () => {
    await setupWith('/trailarr/', '?returnUrl=%2Fmedia');
    signIn();
    expect(window.location.href).toBe('/trailarr/media');
  });

  it('keeps the URL base when no returnUrl is given', async () => {
    await setupWith('/trailarr/', '');
    signIn();
    expect(window.location.href).toBe('/trailarr/home');
  });

  it('redirects to the plain path when no URL base is set', async () => {
    await setupWith('/', '?returnUrl=%2Fmedia');
    signIn();
    expect(window.location.href).toBe('/media');
  });

  it('shows an error and stays on the page when the login fails', async () => {
    await setupWith('/trailarr/', '?returnUrl=%2Fmedia');
    const authService = TestBed.inject(AuthService) as unknown as {login: ReturnType<typeof vi.fn>};
    authService.login.mockReturnValue({subscribe: ({error}: {error: () => void}) => error()});
    signIn();
    fixture.detectChanges();
    expect(window.location.href).toBe('');
    expect((fixture.nativeElement as HTMLElement).querySelector('.error-message')?.textContent).toContain(
      'Invalid username or password.',
    );
  });
});
