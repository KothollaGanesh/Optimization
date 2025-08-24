import { Routes } from '@angular/router';

export const medicalRecordsRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./medical-record-list/medical-record-list.component').then(m => m.MedicalRecordListComponent)
  },
  {
    path: 'create',
    loadComponent: () => import('./medical-record-form/medical-record-form.component').then(m => m.MedicalRecordFormComponent)
  },
  {
    path: ':id',
    loadComponent: () => import('./medical-record-detail/medical-record-detail.component').then(m => m.MedicalRecordDetailComponent)
  },
  {
    path: ':id/edit',
    loadComponent: () => import('./medical-record-form/medical-record-form.component').then(m => m.MedicalRecordFormComponent)
  }
];