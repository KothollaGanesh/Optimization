import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule, MatProgressSpinnerModule],
  template: `
    <div class="loading-overlay">
      <div class="spinner-container">
        <mat-spinner diameter="50"></mat-spinner>
        <p class="loading-text">Loading...</p>
      </div>
    </div>
  `,
  styles: [`
    .loading-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: rgba(255, 255, 255, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
    }

    .spinner-container {
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .loading-text {
      margin-top: 16px;
      color: #666;
      font-weight: 500;
    }
  `]
})
export class LoadingSpinnerComponent {}