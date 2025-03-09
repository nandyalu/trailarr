import { ApplicationConfig, importProvidersFrom } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';

import { DATE_PIPE_DEFAULT_OPTIONS } from '@angular/common';
import { provideHttpClient } from '@angular/common/http';
import { TimeagoModule } from "ngx-timeago";
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(
      // withInterceptors([authInterceptor]),
    ),
    { provide: DATE_PIPE_DEFAULT_OPTIONS, useValue: { dateFormat: 'medium', timezone: 'UTC' } },
    importProvidersFrom(
      TimeagoModule.forRoot()
    )
  ]
};
