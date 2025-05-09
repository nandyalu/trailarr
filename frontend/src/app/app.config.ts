import {DATE_PIPE_DEFAULT_OPTIONS} from '@angular/common';
import {provideHttpClient} from '@angular/common/http';
import {ApplicationConfig, importProvidersFrom} from '@angular/core';
import {PreloadAllModules, provideRouter, withComponentInputBinding, withPreloading, withViewTransitions} from '@angular/router';
import {ApiModule} from 'generated-sources/openapi';
import {TimeagoModule} from 'ngx-timeago';
import {routes} from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes, withComponentInputBinding(), withPreloading(PreloadAllModules), withViewTransitions()),
    provideHttpClient(),
    // withInterceptors([authInterceptor]),
    {provide: DATE_PIPE_DEFAULT_OPTIONS, useValue: {dateFormat: 'medium', timezone: 'UTC'}},
    importProvidersFrom(ApiModule.forRoot({rootUrl: ''}), TimeagoModule.forRoot()),
  ],
};
