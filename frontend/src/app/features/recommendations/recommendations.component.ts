import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FarmService } from '../../core/services/farm.service';
import { ApiService } from '../../core/services/api.service';
import { Recommendation } from '../../core/models/recommendation.model';

@Component({
  selector: 'app-recommendations',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <main>
      <div class="band" style="--b:var(--sv);--t:#000">Mapendekezo</div>

      @if (!farmSvc.selectedFarm()) {
        <div class="empty">Chagua shamba kwanza</div>
      } @else {
        <div class="row">
          <button class="btn o" (click)="generate()" [disabled]="loading()">
            @if (loading()) { <span class="sp"></span>Inatengeneza... }
            @else { Generate Recs }
          </button>
          <span class="mu">{{ status() }}</span>
        </div>

        <label for="filter">Tafuta kwa kichwa, maelezo, kipaumbele au hali</label>
        <input id="filter" type="search" [(ngModel)]="filter" placeholder="Tafuta..." />

        @if (loading()) {
          <div><span class="sp"></span>Inapakia...</div>
        } @else {
          <div class="grid c2">
            @for (r of filtered(); track $index) {
              <div class="card" [style.borderLeft]="'6px solid ' + prioColor(r.priority)">
                <span class="tag" [style.background]="prioColor(r.priority)">{{ r.priority }}</span>
                <b>{{ r.title }}</b>
                @if (r.confidence != null) {
                  <span class="mu"> - uhakika {{ (r.confidence * 100).toFixed(0) }}%</span>
                }
                <p class="mu">{{ r.description }}</p>
                @if (r.reason) {
                  <p class="mu"><b>Sababu:</b> {{ r.reason }}</p>
                }
                @if (r.status) {
                  <p class="mu"><b>Hali:</b> {{ r.status }}</p>
                }
              </div>
            } @empty {
              <div class="card">
                <p class="mu">Hakuna mapendekezo. Bonyeza "Generate Recs" kuanza.</p>
              </div>
            }
          </div>
        }
      }
    </main>
  `,
})
export class RecommendationsComponent {
  farmSvc = inject(FarmService);
  private api = inject(ApiService);

  recs = signal<Recommendation[]>([]);
  loading = signal(false);
  status = signal('');
  filter = '';

  filtered = computed(() => {
    const q = this.filter.trim().toLowerCase();
    return q
      ? this.recs().filter((r) =>
          (r.title + ' ' + r.description + ' ' + r.priority + ' ' + (r.status || ''))
            .toLowerCase()
            .includes(q)
        )
      : this.recs();
  });

  constructor() {
    setTimeout(() => {
      if (this.farmSvc.selectedFarm()) this.load();
    }, 100);
  }

  load() {
    const farm = this.farmSvc.selectedFarm();
    if (!farm) return;
    this.loading.set(true);
    this.status.set('');
    this.api.get<Recommendation[]>(`/api/recommendations/farm/${farm.id}`).subscribe({
      next: (d) => {
        this.recs.set(d ?? []);
        this.loading.set(false);
      },
      error: () => {
        this.recs.set([]);
        this.loading.set(false);
      },
    });
  }

  generate() {
    const farm = this.farmSvc.selectedFarm();
    if (!farm) return;
    this.loading.set(true);
    this.status.set('Inatengeneza mapendekezo...');
    this.api.post(`/api/recommendations/farm/${farm.id}/generate`, {}).subscribe({
      next: () => {
        this.status.set('✅ Mapendekezo yametengenezwa');
        this.load();
        setTimeout(() => this.status.set(''), 3000);
      },
      error: (e: any) => {
        this.loading.set(false);
        this.status.set('❌ Imeshindwa: ' + e.message);
      },
    });
  }

  prioColor(p: string): string {
    const map: Record<string, string> = {
      HIGH: '#b00020', MEDIUM: '#FF6B35', LOW: '#228B22',
    };
    return map[p] ?? '#8B4513';
  }
}
