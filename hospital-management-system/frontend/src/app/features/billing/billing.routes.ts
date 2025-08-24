import { Routes } from '@angular/router';

export const billingRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./billing-list/billing-list.component').then(m => m.BillingListComponent)
  },
  {
    path: 'create',
    loadComponent: () => import('./billing-form/billing-form.component').then(m => m.BillingFormComponent)
  },
  {
    path: ':id',
    loadComponent: () => import('./billing-detail/billing-detail.component').then(m => m.BillingDetailComponent)
  }
];