import { Routes } from '@angular/router';

export const adminRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./admin-dashboard/admin-dashboard.component').then(m => m.AdminDashboardComponent)
  },
  {
    path: 'users',
    loadComponent: () => import('./user-management/user-management.component').then(m => m.UserManagementComponent)
  },
  {
    path: 'departments',
    loadComponent: () => import('./department-management/department-management.component').then(m => m.DepartmentManagementComponent)
  },
  {
    path: 'services',
    loadComponent: () => import('./service-management/service-management.component').then(m => m.ServiceManagementComponent)
  },
  {
    path: 'reports',
    loadComponent: () => import('./reports/reports.component').then(m => m.ReportsComponent)
  },
  {
    path: 'system',
    loadComponent: () => import('./system-settings/system-settings.component').then(m => m.SystemSettingsComponent)
  }
];