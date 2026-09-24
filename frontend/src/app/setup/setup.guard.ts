import {inject} from '@angular/core';
import {CanActivateFn, Router} from '@angular/router';
import {catchError, map, of, switchMap} from 'rxjs';
import {RouteHome, RouteSetup} from 'src/routing';
import {AuthService} from '../services/auth.service';
import {SetupService} from '../services/setup.service';

/**
 * Ask the server about the setup, after the session exists.
 *
 * Angular runs the guards of a route at the same time, so asking straight
 * away races `authGuard`: with the web UI login turned off, the session
 * cookie is minted by the very call that guard makes, and the setup
 * request went out without it and came back 401. Waiting for the auth
 * check first costs nothing — it is cached for a minute — and removes the
 * race.
 */
function setupStatus() {
  const authService = inject(AuthService);
  const setupService = inject(SetupService);
  const known = setupService.status();
  if (known) {
    return of(known);
  }
  return authService.checkAuthStatus().pipe(
    switchMap((authenticated) => (authenticated ? setupService.loadStatus() : of(null))),
  );
}

/**
 * Sends a fresh installation to the setup guide, once.
 *
 * The server decides, not the browser: it records the decision the first
 * time it starts, so an installation that is already in use never lands
 * here, not even after its last connection is removed (wargame C1).
 *
 * A failure to ask is not a reason to block anybody, so the app loads.
 */
export const setupRedirectGuard: CanActivateFn = () => {
  const router = inject(Router);
  return setupStatus().pipe(
    map((status) => (status?.needed ? router.createUrlTree([RouteSetup]) : true)),
    catchError(() => of(true)),
  );
};

/** Keeps the guide itself out of reach once setup is behind you. */
export const setupOnlyWhenNeededGuard: CanActivateFn = () => {
  const router = inject(Router);
  return setupStatus().pipe(
    map((status) => (status?.needed ? true : router.createUrlTree([RouteHome]))),
    catchError(() => of(router.createUrlTree([RouteHome]))),
  );
};
