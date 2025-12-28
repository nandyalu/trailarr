import {DATE_PIPE_DEFAULT_OPTIONS} from '@angular/common';
import {provideHttpClient} from '@angular/common/http';
import {ApplicationConfig, ErrorHandler, importProvidersFrom} from '@angular/core';
import {PreloadAllModules, provideRouter, withComponentInputBinding, withInMemoryScrolling, withPreloading} from '@angular/router';
import {ApiModule} from 'generated-sources/openapi';
import {TimeagoModule} from 'ngx-timeago';
import {routes} from './app.routes';
import {GlobalErrorHandler} from './error-handler';
import {provideSignalFormsConfig} from '@angular/forms/signals';
import {NG_STATUS_CLASSES} from '@angular/forms/signals/compat';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(
      routes,
      withComponentInputBinding(),
      withPreloading(PreloadAllModules),
      // withViewTransitions(),
      withInMemoryScrolling({scrollPositionRestoration: 'top', anchorScrolling: 'enabled'}),
    ),
    provideSignalFormsConfig({classes: NG_STATUS_CLASSES}),
    {provide: ErrorHandler, useClass: GlobalErrorHandler},
    provideHttpClient(),
    // withInterceptors([authInterceptor]),
    {provide: DATE_PIPE_DEFAULT_OPTIONS, useValue: {dateFormat: 'medium', timezone: 'UTC'}},
    importProvidersFrom(ApiModule.forRoot({rootUrl: ''}), TimeagoModule.forRoot()),
  ],
};
