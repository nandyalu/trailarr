// src/app/global-error-handler.ts
import {ErrorHandler, Injectable} from '@angular/core';
import {throwError} from 'rxjs';

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  handleError(error: any) {
    let errorMessage = '';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Client Error: ${error.error.message}`;
    } else {
      // Server-side error (FastAPI)
      const detail = error.error?.detail;
      const message = error.error?.message;
      const fallback = error.message || 'Unknown error occurred';

      errorMessage = `Server Error (${error.status}): ${detail || message || fallback}`;
    }

    // Throw an actual Error object with the message
    return throwError(() => new Error(errorMessage));
  }
}
