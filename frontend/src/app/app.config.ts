import {DATE_PIPE_DEFAULT_OPTIONS} from '@angular/common';
import {provideHttpClient} from '@angular/common/http';
import {ApplicationConfig, ErrorHandler, provideZonelessChangeDetection} from '@angular/core';
import {provideSignalFormsConfig} from '@angular/forms/signals';
import {NG_STATUS_CLASSES} from '@angular/forms/signals/compat';
import {
  PreloadAllModules,
  provideRouter,
  withComponentInputBinding,
  withInMemoryScrolling,
  withPreloading,
  withViewTransitions,
} from '@angular/router';
import {routes} from './app.routes';
import {GlobalErrorHandler} from './error-handler';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideRouter(
      routes,
      withComponentInputBinding(),
      withPreloading(PreloadAllModules),
      withViewTransitions({skipInitialTransition: true}),
      withInMemoryScrolling({scrollPositionRestoration: 'enabled', anchorScrolling: 'enabled'}),
    ),
    provideSignalFormsConfig({classes: NG_STATUS_CLASSES}),
    {provide: ErrorHandler, useClass: GlobalErrorHandler},
    provideHttpClient(),
    // withInterceptors([authInterceptor]),
    // Dates are stored and sent as UTC; the `date` pipe must render them in
    // the VIEWER's timezone. Do not set `timezone` here — pinning it to 'UTC'
    // made every date show UTC clock time regardless of the user's timezone.
    {provide: DATE_PIPE_DEFAULT_OPTIONS, useValue: {dateFormat: 'medium'}},
  ],
};
