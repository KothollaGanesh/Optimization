import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { Router } from '@angular/router';

import { 
  User, 
  LoginRequest, 
  LoginResponse, 
  RegisterPatientRequest, 
  ChangePasswordRequest 
} from '../../shared/models/user.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly API_URL = '/api/auth';
  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly USER_KEY = 'current_user';

  private currentUserSubject = new BehaviorSubject<User | null>(null);
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(false);

  public currentUser$ = this.currentUserSubject.asObservable();
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  constructor(
    private http: HttpClient,
    private router: Router
  ) {}

  /**
   * Initialize auth state from localStorage
   */
  initializeAuthState(): void {
    const token = this.getToken();
    const user = this.getCurrentUser();
    
    if (token && user) {
      this.currentUserSubject.next(user);
      this.isAuthenticatedSubject.next(true);
    } else {
      this.clearAuthData();
    }
  }

  /**
   * Login user
   */
  login(credentials: LoginRequest): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.API_URL}/login`, credentials)
      .pipe(
        tap(response => {
          this.setAuthData(response);
        }),
        catchError(error => {
          console.error('Login error:', error);
          return throwError(() => error);
        })
      );
  }

  /**
   * Register new patient
   */
  registerPatient(data: RegisterPatientRequest): Observable<any> {
    return this.http.post(`${this.API_URL}/register/patient`, data)
      .pipe(
        catchError(error => {
          console.error('Registration error:', error);
          return throwError(() => error);
        })
      );
  }

  /**
   * Logout user
   */
  logout(): Observable<any> {
    return this.http.post(`${this.API_URL}/logout`, {})
      .pipe(
        tap(() => {
          this.clearAuthData();
          this.router.navigate(['/auth/login']);
        }),
        catchError(error => {
          // Even if logout fails on server, clear local data
          this.clearAuthData();
          this.router.navigate(['/auth/login']);
          return throwError(() => error);
        })
      );
  }

  /**
   * Refresh access token
   */
  refreshToken(): Observable<any> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return throwError(() => new Error('No refresh token available'));
    }

    return this.http.post(`${this.API_URL}/refresh`, {})
      .pipe(
        tap((response: any) => {
          this.setToken(response.access_token);
        }),
        catchError(error => {
          this.clearAuthData();
          this.router.navigate(['/auth/login']);
          return throwError(() => error);
        })
      );
  }

  /**
   * Get current user profile
   */
  getProfile(): Observable<any> {
    return this.http.get(`${this.API_URL}/profile`)
      .pipe(
        tap((response: any) => {
          this.currentUserSubject.next(response.user);
          this.setCurrentUser(response.user);
        }),
        catchError(error => {
          console.error('Get profile error:', error);
          return throwError(() => error);
        })
      );
  }

  /**
   * Change password
   */
  changePassword(data: ChangePasswordRequest): Observable<any> {
    return this.http.post(`${this.API_URL}/change-password`, data)
      .pipe(
        catchError(error => {
          console.error('Change password error:', error);
          return throwError(() => error);
        })
      );
  }

  /**
   * Verify if token is valid
   */
  verifyToken(): Observable<any> {
    return this.http.post(`${this.API_URL}/verify-token`, {})
      .pipe(
        catchError(error => {
          this.clearAuthData();
          return throwError(() => error);
        })
      );
  }

  /**
   * Get stored token
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Get stored refresh token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Get current user from localStorage
   */
  getCurrentUser(): User | null {
    const userJson = localStorage.getItem(this.USER_KEY);
    if (userJson) {
      try {
        return JSON.parse(userJson);
      } catch (error) {
        console.error('Error parsing user data:', error);
        return null;
      }
    }
    return null;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getToken() && !!this.getCurrentUser();
  }

  /**
   * Check if user has specific role
   */
  hasRole(role: string): boolean {
    const user = this.getCurrentUser();
    return user ? user.role === role : false;
  }

  /**
   * Check if user has any of the specified roles
   */
  hasAnyRole(roles: string[]): boolean {
    const user = this.getCurrentUser();
    return user ? roles.includes(user.role) : false;
  }

  /**
   * Set authentication data
   */
  private setAuthData(response: LoginResponse): void {
    localStorage.setItem(this.TOKEN_KEY, response.access_token);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, response.refresh_token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
    
    this.currentUserSubject.next(response.user);
    this.isAuthenticatedSubject.next(true);
  }

  /**
   * Set token
   */
  private setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  /**
   * Set current user
   */
  private setCurrentUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  /**
   * Clear all authentication data
   */
  private clearAuthData(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    
    this.currentUserSubject.next(null);
    this.isAuthenticatedSubject.next(false);
  }
}