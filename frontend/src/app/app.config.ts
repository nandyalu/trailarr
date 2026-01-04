import {DATE_PIPE_DEFAULT_OPTIONS} from '@angular/common';
import {provideHttpClient} from '@angular/common/http';
import {ApplicationConfig, ErrorHandler, importProvidersFrom, provideZonelessChangeDetection} from '@angular/core';
import {provideSignalFormsConfig} from '@angular/forms/signals';
import {NG_STATUS_CLASSES} from '@angular/forms/signals/compat';
import {PreloadAllModules, provideRouter, withComponentInputBinding, withInMemoryScrolling, withPreloading, withViewTransitions} from '@angular/router';
import {ApiModule} from 'generated-sources/openapi';
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
      withInMemoryScrolling({scrollPositionRestoration: 'top', anchorScrolling: 'enabled'}),
    ),
    provideSignalFormsConfig({classes: NG_STATUS_CLASSES}),
    {provide: ErrorHandler, useClass: GlobalErrorHandler},
    provideHttpClient(),
    // withInterceptors([authInterceptor]),
    {provide: DATE_PIPE_DEFAULT_OPTIONS, useValue: {dateFormat: 'medium', timezone: 'UTC'}},
    importProvidersFrom(ApiModule.forRoot({rootUrl: ''})),
  ],
};
