import { Routes } from '@angular/router';

export const doctorsRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./doctor-list/doctor-list.component').then(m => m.DoctorListComponent)
  },
  {
    path: 'create',
    loadComponent: () => import('./doctor-form/doctor-form.component').then(m => m.DoctorFormComponent)
  },
  {
    path: ':id',
    loadComponent: () => import('./doctor-detail/doctor-detail.component').then(m => m.DoctorDetailComponent)
  },
  {
    path: ':id/edit',
    loadComponent: () => import('./doctor-form/doctor-form.component').then(m => m.DoctorFormComponent)
  }
];