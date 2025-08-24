import { Routes } from '@angular/router';

export const appointmentsRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./appointment-list/appointment-list.component').then(m => m.AppointmentListComponent)
  },
  {
    path: 'create',
    loadComponent: () => import('./appointment-form/appointment-form.component').then(m => m.AppointmentFormComponent)
  },
  {
    path: ':id',
    loadComponent: () => import('./appointment-detail/appointment-detail.component').then(m => m.AppointmentDetailComponent)
  },
  {
    path: ':id/edit',
    loadComponent: () => import('./appointment-form/appointment-form.component').then(m => m.AppointmentFormComponent)
  }
];