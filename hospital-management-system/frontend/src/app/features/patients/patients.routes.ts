import { Routes } from '@angular/router';

export const patientsRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./patient-list/patient-list.component').then(m => m.PatientListComponent)
  },
  {
    path: 'create',
    loadComponent: () => import('./patient-form/patient-form.component').then(m => m.PatientFormComponent)
  },
  {
    path: ':id',
    loadComponent: () => import('./patient-detail/patient-detail.component').then(m => m.PatientDetailComponent)
  },
  {
    path: ':id/edit',
    loadComponent: () => import('./patient-form/patient-form.component').then(m => m.PatientFormComponent)
  }
];