import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { Router } from '@angular/router';

import { AuthService } from '../services/auth.service';
import { LoadingService } from '../services/loading.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const loadingService = inject(LoadingService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      loadingService.hide(); // Hide loading on error

      if (error.status === 401) {
        // Try to refresh token
        const refreshToken = authService.getRefreshToken();
        if (refreshToken && !req.url.includes('/refresh')) {
          return authService.refreshToken().pipe(
            switchMap(() => {
              // Retry the original request with new token
              const token = authService.getToken();
              const authReq = req.clone({
                headers: req.headers.set('Authorization', `Bearer ${token}`)
              });
              return next(authReq);
            }),
            catchError(() => {
              // Refresh failed, redirect to login
              router.navigate(['/auth/login']);
              return throwError(() => error);
            })
          );
        } else {
          // No refresh token or refresh endpoint, redirect to login
          router.navigate(['/auth/login']);
        }
      }

      if (error.status === 403) {
        // Access denied, redirect to dashboard
        router.navigate(['/dashboard']);
      }

      return throwError(() => error);
    })
  );
};