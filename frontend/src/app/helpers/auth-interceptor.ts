import { HttpHandlerFn, HttpRequest } from "@angular/common/http";
import { inject } from "@angular/core";
import { switchMap } from "rxjs";
import { AuthService } from "../services/auth.service";

export function authInterceptor(req: HttpRequest<unknown>, next: HttpHandlerFn) {
    // Skip the interceptor for the login endpoint.
    if (req.url.includes('login')) {
        return next(req);
    }
    // Inject the current `AuthService` and use it to get an authentication token:
    let api_key = sessionStorage.getItem('api_key') || '';
    if (api_key === '') {
        // If the API key is not stored in the session storage, get it from the server.
        return inject(AuthService).getApiKey().pipe(
            switchMap((key) => {
                // Store the API key in the session storage and make original API call with API Key.
                sessionStorage.setItem('api_key', key);
                return handleRequest(req, next, key);
            })
        );
    } else {
        // If the API key is stored in the session storage, make the original API call with API Key.
        return handleRequest(req, next, api_key);
    }
}

function handleRequest(req: HttpRequest<unknown>, next: HttpHandlerFn, api_key: string) {
    // Clone the request to add the API Key in header and make the request.
    const newReq = req.clone({
        headers: req.headers.set('X-API-KEY', api_key),
    });
    return next(newReq);
};