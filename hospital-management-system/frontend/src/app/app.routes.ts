import { Routes } from '@angular/router';
import { AuthGuard } from './core/guards/auth.guard';
import { GuestGuard } from './core/guards/guest.guard';
import { RoleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'auth',
    canActivate: [GuestGuard],
    loadChildren: () => import('./features/auth/auth.routes').then(m => m.authRoutes)
  },
  {
    path: 'dashboard',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/dashboard/dashboard.routes').then(m => m.dashboardRoutes)
  },
  {
    path: 'patients',
    canActivate: [AuthGuard, RoleGuard],
    data: { roles: ['admin', 'doctor', 'receptionist', 'patient'] },
    loadChildren: () => import('./features/patients/patients.routes').then(m => m.patientsRoutes)
  },
  {
    path: 'doctors',
    canActivate: [AuthGuard, RoleGuard],
    data: { roles: ['admin', 'receptionist', 'patient'] },
    loadChildren: () => import('./features/doctors/doctors.routes').then(m => m.doctorsRoutes)
  },
  {
    path: 'appointments',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/appointments/appointments.routes').then(m => m.appointmentsRoutes)
  },
  {
    path: 'medical-records',
    canActivate: [AuthGuard, RoleGuard],
    data: { roles: ['admin', 'doctor', 'patient'] },
    loadChildren: () => import('./features/medical-records/medical-records.routes').then(m => m.medicalRecordsRoutes)
  },
  {
    path: 'billing',
    canActivate: [AuthGuard, RoleGuard],
    data: { roles: ['admin', 'receptionist', 'patient'] },
    loadChildren: () => import('./features/billing/billing.routes').then(m => m.billingRoutes)
  },
  {
    path: 'admin',
    canActivate: [AuthGuard, RoleGuard],
    data: { roles: ['admin'] },
    loadChildren: () => import('./features/admin/admin.routes').then(m => m.adminRoutes)
  },
  {
    path: '**',
    redirectTo: '/dashboard'
  }
];