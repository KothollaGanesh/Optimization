import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';

import { AuthService } from '../../core/services/auth.service';
import { User } from '../../shared/models/user.model';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    CommonModule, 
    MatToolbarModule, 
    MatIconModule, 
    MatButtonModule, 
    MatMenuModule
  ],
  template: `
    <mat-toolbar class="header-toolbar">
      <div class="header-content">
        <div class="header-left">
          <button mat-icon-button class="menu-toggle" (click)="toggleSidebar()">
            <mat-icon>menu</mat-icon>
          </button>
          <span class="page-title">{{ getPageTitle() }}</span>
        </div>
        
        <div class="header-right">
          <!-- Notifications -->
          <button mat-icon-button [matMenuTriggerFor]="notificationMenu">
            <mat-icon matBadge="3" matBadgeColor="warn">notifications</mat-icon>
          </button>
          
          <!-- User Menu -->
          <button mat-icon-button [matMenuTriggerFor]="userMenu" *ngIf="currentUser">
            <mat-icon>account_circle</mat-icon>
          </button>
        </div>
      </div>
    </mat-toolbar>

    <!-- Notification Menu -->
    <mat-menu #notificationMenu="matMenu">
      <div class="notification-header">
        <h4>Notifications</h4>
      </div>
      <mat-divider></mat-divider>
      <button mat-menu-item>
        <mat-icon>event</mat-icon>
        <span>Appointment reminder at 2:00 PM</span>
      </button>
      <button mat-menu-item>
        <mat-icon>medical_services</mat-icon>
        <span>Lab results available</span>
      </button>
      <button mat-menu-item>
        <mat-icon>receipt</mat-icon>
        <span>Payment due in 3 days</span>
      </button>
      <mat-divider></mat-divider>
      <button mat-menu-item class="view-all">
        <span>View all notifications</span>
      </button>
    </mat-menu>

    <!-- User Menu -->
    <mat-menu #userMenu="matMenu">
      <div class="user-menu-header" *ngIf="currentUser">
        <div class="user-info">
          <strong>{{ currentUser.full_name }}</strong>
          <span class="user-email">{{ currentUser.email }}</span>
        </div>
      </div>
      <mat-divider></mat-divider>
      <button mat-menu-item (click)="viewProfile()">
        <mat-icon>person</mat-icon>
        <span>My Profile</span>
      </button>
      <button mat-menu-item (click)="changePassword()">
        <mat-icon>lock</mat-icon>
        <span>Change Password</span>
      </button>
      <button mat-menu-item>
        <mat-icon>settings</mat-icon>
        <span>Settings</span>
      </button>
      <mat-divider></mat-divider>
      <button mat-menu-item (click)="logout()">
        <mat-icon>logout</mat-icon>
        <span>Logout</span>
      </button>
    </mat-menu>
  `,
  styles: [`
    .header-toolbar {
      background-color: white;
      color: #333;
      border-bottom: 1px solid #e0e0e0;
      height: 64px;
      padding: 0;
    }

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
      padding: 0 16px;
    }

    .header-left {
      display: flex;
      align-items: center;
      
      .menu-toggle {
        margin-right: 16px;
        
        @media (min-width: 769px) {
          display: none;
        }
      }
      
      .page-title {
        font-size: 1.25rem;
        font-weight: 500;
        color: #2c5aa0;
      }
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .notification-header {
      padding: 12px 16px 8px;
      
      h4 {
        margin: 0;
        font-size: 1rem;
        font-weight: 500;
      }
    }

    .user-menu-header {
      padding: 12px 16px 8px;
      
      .user-info {
        display: flex;
        flex-direction: column;
        
        strong {
          font-size: 0.95rem;
        }
        
        .user-email {
          font-size: 0.8rem;
          color: #666;
          margin-top: 2px;
        }
      }
    }

    .view-all {
      text-align: center;
      font-weight: 500;
      color: #2c5aa0;
    }

    mat-menu-item {
      font-size: 0.9rem;
      
      mat-icon {
        margin-right: 8px;
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
    }
  `]
})
export class HeaderComponent implements OnInit {
  currentUser: User | null = null;

  constructor(private authService: AuthService) {}

  ngOnInit() {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
    });
  }

  getPageTitle(): string {
    // You can implement logic to get current page title based on route
    // For now, return a default title
    return 'Hospital Management System';
  }

  toggleSidebar() {
    // Implement sidebar toggle logic for mobile
    // This would typically emit an event to parent component
  }

  viewProfile() {
    // Navigate to profile page
    console.log('View profile clicked');
  }

  changePassword() {
    // Open change password dialog
    console.log('Change password clicked');
  }

  logout() {
    this.authService.logout().subscribe();
  }
}