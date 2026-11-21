import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FarmService } from '../../core/services/farm.service';
import { AuthService } from '../../core/services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-farms',
  standalone: true,
  imports: [CommonModule],
  template: `
    <main>
      <div class="band" style="--b:var(--g);--t:#000">Usimamizi wa Mashamba</div>
      <div class="card">
        <div class="row">
          @if (auth.canAct()) {
            <span class="mu">{{ farmSvc.farms().length }} mashamba</span>
          }
        </div>
        <div class="wrap">
          <table>
            <thead><tr><th>Shamba</th><th>Mkulima</th><th>Mkoa</th><th>Eneo (ha)</th><th>Chagua</th></tr></thead>
            <tbody>
              @for (f of farmSvc.farms(); track f.id) {
                <tr>
                  <td>{{ f.name }}</td>
                  <td>{{ farmSvc.farmerName(f) || '-' }}</td>
                  <td>{{ farmSvc.regionOf(f) || '-' }}</td>
                  <td>{{ f.areaHa ?? '-' }}</td>
                  <td>
                    <button class="btn" (click)="select(f)">Fungua</button>
                  </td>
                </tr>
              } @empty {
                <tr><td colspan="5" class="mu">Hakuna mashamba</td></tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    </main>
  `,
})
export class FarmsComponent {
  farmSvc = inject(FarmService);
  auth = inject(AuthService);
  private router = inject(Router);

  select(f: any) {
    this.farmSvc.select(f);
    this.router.navigate(['/dash']);
  }
}
