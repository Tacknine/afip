import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FarmService } from '../../core/services/farm.service';
import { ApiService } from '../../core/services/api.service';
import { SoilProperty } from '../../core/models/soil.model';

@Component({
  selector: 'app-soil',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <main>
      <div class="band" style="--b:var(--br);--t:#fff">Udongo (Soil)</div>
      @if (!farmSvc.selectedFarm()) {
        <div class="empty">Chagua shamba kwanza</div>
      } @else {
        <div class="card">
          <div class="row">
            <label class="mu" style="margin:0">Kina (cm)</label>
            <select class="sel" [(ngModel)]="selectedDepth" (change)="load()">
              @for (d of depths(); track d) {
                <option [value]="d">{{ d }}</option>
              }
            </select>
            <button class="btn needs-act" (click)="fetchSoil()" [disabled]="loading()">
              Fetch Soil
            </button>
          </div>
          @if (loading()) { <div><span class="sp"></span>Inapakia...</div> }
          <div class="wrap">
            @if (soil().length === 0) {
              <p class="mu">Hakuna data ya udongo</p>
            } @else {
              <table>
                <thead><tr><th>Kipimo</th><th>Thamani</th><th>Kina</th><th>Chanzo</th></tr></thead>
                <tbody>
                  @for (s of soil(); track s.property) {
                    <tr>
                      <td>{{ s.property }}</td>
                      <td><b>{{ s.value }}</b></td>
                      <td>{{ s.depth || '-' }}</td>
                      <td class="mu">{{ s.unit || '' }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            }
          </div>
        </div>
      }
    </main>
  `,
})
export class SoilComponent {
  farmSvc = inject(FarmService);
  private api = inject(ApiService);

  soil = signal<SoilProperty[]>([]);
  loading = signal(false);
  selectedDepth = '0-20';

  depths = computed(() => {
    const ds = [...new Set(this.soil().map((s) => s.depth).filter(Boolean))];
    return ds.length ? ds : ['0-20'];
  });

  constructor() {
    // Auto-load when farm selected
    setTimeout(() => {
      if (this.farmSvc.selectedFarm()) this.load();
    }, 100);
  }

  load() {
    const farm = this.farmSvc.selectedFarm();
    if (!farm) return;
    this.loading.set(true);
    this.api.get<SoilProperty[]>(`/api/soil/farm/${farm.id}`).subscribe({
      next: (d) => {
        this.soil.set(d ?? []);
        this.loading.set(false);
      },
      error: () => {
        this.soil.set([]);
        this.loading.set(false);
      },
    });
  }

  fetchSoil() {
    const farm = this.farmSvc.selectedFarm();
    if (!farm) return;
    this.loading.set(true);
    this.api
      .post(`/api/soil/farm/${farm.id}/fetch?depth=${encodeURIComponent(this.selectedDepth)}`, {})
      .subscribe({
        next: () => this.load(),
        error: () => this.loading.set(false),
      });
  }
}
