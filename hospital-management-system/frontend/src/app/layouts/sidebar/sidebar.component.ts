import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';

import { AuthService } from '../../core/services/auth.service';
import { User, UserRole } from '../../shared/models/user.model';

interface MenuItem {
  label: string;
  icon: string;
  route: string;
  roles: string[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule, MatListModule],
  template: `
    <div class="sidebar">
      <div class="logo">
        <mat-icon>local_hospital</mat-icon>
        <h2>MedCare HMS</h2>
      </div>
      
      <nav class="nav-menu">
        <mat-nav-list>
          <mat-list-item 
            *ngFor="let item of visibleMenuItems" 
            [routerLink]="item.route"
            routerLinkActive="active">
            <mat-icon matListItemIcon>{{ item.icon }}</mat-icon>
            <span matListItemTitle>{{ item.label }}</span>
          </mat-list-item>
        </mat-nav-list>
      </nav>
      
      <div class="sidebar-footer">
        <div class="user-info" *ngIf="currentUser">
          <mat-icon>account_circle</mat-icon>
          <div class="user-details">
            <span class="user-name">{{ currentUser.full_name }}</span>
            <span class="user-role">{{ getRoleDisplayName(currentUser.role) }}</span>
          </div>
        </div>
        
        <button class="logout-btn" (click)="logout()">
          <mat-icon>logout</mat-icon>
          <span>Logout</span>
        </button>
      </div>
    </div>
  `,
  styles: [`
    .sidebar {
      width: 250px;
      height: 100vh;
      background-color: #2c5aa0;
      color: white;
      display: flex;
      flex-direction: column;
      overflow-y: auto;
    }

    .logo {
      display: flex;
      align-items: center;
      padding: 20px;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      
      mat-icon {
        margin-right: 10px;
        font-size: 28px;
        width: 28px;
        height: 28px;
      }
      
      h2 {
        margin: 0;
        font-size: 1.2rem;
        font-weight: 600;
      }
    }

    .nav-menu {
      flex: 1;
      padding: 10px 0;
      
      mat-nav-list {
        padding: 0;
      }
      
      mat-list-item {
        color: white;
        margin: 2px 10px;
        border-radius: 6px;
        
        &:hover, &.active {
          background-color: rgba(255,255,255,0.1);
        }
        
        mat-icon {
          color: white;
          margin-right: 10px;
        }
      }
    }

    .sidebar-footer {
      padding: 20px;
      border-top: 1px solid rgba(255,255,255,0.1);
      
      .user-info {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        
        mat-icon {
          margin-right: 10px;
          font-size: 24px;
        }
        
        .user-details {
          display: flex;
          flex-direction: column;
          
          .user-name {
            font-weight: 500;
            font-size: 0.9rem;
          }
          
          .user-role {
            font-size: 0.75rem;
            opacity: 0.8;
            text-transform: capitalize;
          }
        }
      }
      
      .logout-btn {
        display: flex;
        align-items: center;
        background: none;
        border: 1px solid rgba(255,255,255,0.3);
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
        font-size: 0.9rem;
        
        &:hover {
          background-color: rgba(255,255,255,0.1);
        }
        
        mat-icon {
          margin-right: 8px;
          font-size: 18px;
        }
      }
    }

    @media (max-width: 768px) {
      .sidebar {
        position: fixed;
        z-index: 1000;
        transform: translateX(-100%);
        transition: transform 0.3s ease;
        
        &.open {
          transform: translateX(0);
        }
      }
    }
  `]
})
export class SidebarComponent implements OnInit {
  currentUser: User | null = null;
  visibleMenuItems: MenuItem[] = [];

  private menuItems: MenuItem[] = [
    { label: 'Dashboard', icon: 'dashboard', route: '/dashboard', roles: ['admin', 'doctor', 'patient', 'receptionist'] },
    { label: 'Patients', icon: 'people', route: '/patients', roles: ['admin', 'doctor', 'receptionist', 'patient'] },
    { label: 'Doctors', icon: 'medical_services', route: '/doctors', roles: ['admin', 'receptionist', 'patient'] },
    { label: 'Appointments', icon: 'event', route: '/appointments', roles: ['admin', 'doctor', 'patient', 'receptionist'] },
    { label: 'Medical Records', icon: 'description', route: '/medical-records', roles: ['admin', 'doctor', 'patient'] },
    { label: 'Billing', icon: 'receipt', route: '/billing', roles: ['admin', 'receptionist', 'patient'] },
    { label: 'Administration', icon: 'admin_panel_settings', route: '/admin', roles: ['admin'] }
  ];

  constructor(private authService: AuthService) {}

  ngOnInit() {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
      this.updateVisibleMenuItems();
    });
  }

  private updateVisibleMenuItems() {
    if (this.currentUser) {
      this.visibleMenuItems = this.menuItems.filter(item => 
        item.roles.includes(this.currentUser!.role)
      );
    } else {
      this.visibleMenuItems = [];
    }
  }

  getRoleDisplayName(role: string): string {
    switch (role) {
      case UserRole.ADMIN:
        return 'Administrator';
      case UserRole.DOCTOR:
        return 'Doctor';
      case UserRole.PATIENT:
        return 'Patient';
      case UserRole.RECEPTIONIST:
        return 'Receptionist';
      default:
        return role;
    }
  }

  logout() {
    this.authService.logout().subscribe();
  }
}