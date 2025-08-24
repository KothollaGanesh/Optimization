import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';

import { AuthService } from './core/services/auth.service';
import { LoadingService } from './core/services/loading.service';
import { SidebarComponent } from './layouts/sidebar/sidebar.component';
import { HeaderComponent } from './layouts/header/header.component';
import { LoadingSpinnerComponent } from './shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule, 
    RouterOutlet, 
    SidebarComponent, 
    HeaderComponent, 
    LoadingSpinnerComponent
  ],
  template: `
    <div class="main-container">
      <!-- Loading Spinner -->
      <app-loading-spinner *ngIf="loadingService.loading$ | async"></app-loading-spinner>
      
      <!-- Auth Layout (Login/Register) -->
      <div *ngIf="isAuthRoute" class="auth-layout">
        <router-outlet></router-outlet>
      </div>
      
      <!-- Main Application Layout -->
      <div *ngIf="!isAuthRoute && isLoggedIn" class="app-layout d-flex">
        <app-sidebar class="sidebar-container"></app-sidebar>
        <div class="content-wrapper flex-grow-1">
          <app-header></app-header>
          <main class="content-area">
            <router-outlet></router-outlet>
          </main>
        </div>
      </div>
      
      <!-- Fallback for unauthenticated users not on auth routes -->
      <div *ngIf="!isAuthRoute && !isLoggedIn" class="unauthorized-layout">
        <div class="text-center mt-5">
          <h2>Access Denied</h2>
          <p>Please log in to access the application.</p>
          <button class="btn btn-primary" (click)="goToLogin()">Go to Login</button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .main-container {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    
    .auth-layout {
      height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .app-layout {
      height: 100vh;
    }
    
    .sidebar-container {
      width: 250px;
      flex-shrink: 0;
    }
    
    .content-wrapper {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    
    .content-area {
      flex: 1;
      overflow-y: auto;
      background-color: #f8f9fa;
    }
    
    .unauthorized-layout {
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #f8f9fa;
    }
    
    @media (max-width: 768px) {
      .sidebar-container {
        position: fixed;
        z-index: 1000;
        height: 100%;
        transform: translateX(-100%);
        transition: transform 0.3s ease;
      }
      
      .sidebar-container.open {
        transform: translateX(0);
      }
    }
  `]
})
export class AppComponent implements OnInit {
  title = 'MedCare Hospital Management System';
  isAuthRoute = false;
  isLoggedIn = false;

  constructor(
    private router: Router,
    private authService: AuthService,
    public loadingService: LoadingService
  ) {}

  ngOnInit() {
    // Check authentication status
    this.authService.isAuthenticated$.subscribe(isAuth => {
      this.isLoggedIn = isAuth;
    });

    // Listen to route changes to determine layout
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        this.isAuthRoute = event.url.startsWith('/auth');
      });

    // Check initial route
    this.isAuthRoute = this.router.url.startsWith('/auth');

    // Initialize auth state
    this.authService.initializeAuthState();
  }

  goToLogin() {
    this.router.navigate(['/auth/login']);
  }
}