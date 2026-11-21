import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FarmService } from '../../core/services/farm.service';
import { ApiService } from '../../core/services/api.service';
import { Risk } from '../../core/models/risk.model';

@Component({
  selector: 'app-risk',
  standalone: true,
  imports: [CommonModule],
  template: `
    <main>
      <div class="band" style="--b:var(--sn);--t:#000">Hatari</div>

      @if (!farmSvc.selectedFarm()) {
        <div class="empty">Chagua shamba kwanza</div>
      } @else {
        <div class="row">
          <button class="btn o" (click)="assess()" [disabled]="loading()">
            @if (loading()) { <span class="sp"></span>Inakagua... }
            @else { Assess Risk }
          </button>
          <span class="mu">{{ status() }}</span>
        </div>

        @if (loading()) {
          <div><span class="sp"></span>Inapakia...</div>
        } @else {
          <div class="grid c2">
            @for (r of risk(); track $index) {
              <div class="card" [style.borderLeft]="'6px solid ' + sevColor(r.severity)">
                <span class="tag" [style.background]="sevColor(r.severity)">{{ r.severity }}</span>
                <b>{{ (r.riskCategory || '').replace(/_/g, ' ') }}</b>
                <p class="mu">{{ r.recommendedAction }}</p>
                @if (r.confidence != null) {
                  <p class="mu">Uhakika: {{ (r.confidence * 100).toFixed(0) }}%</p>
                }
              </div>
            } @empty {
              <div class="card"><p class="mu">Hakuna hatari. Bonyeza "Assess Risk" kuanza.</p></div>
            }
          </div>
        }
      }
    </main>
  `,
})
export class RiskComponent {
  farmSvc = inject(FarmService);
  private api = inject(ApiService);

  risk = signal<Risk[]>([]);
  loading = signal(false);
  status = signal('');

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
    this.api.get<Risk[]>(`/api/risk/farm/${farm.id}`).subscribe({
      next: (d) => {
        this.risk.set(d ?? []);
        this.loading.set(false);
      },
      error: () => {
        this.risk.set([]);
        this.loading.set(false);
      },
    });
  }

  assess() {
    const farm = this.farmSvc.selectedFarm();
    if (!farm) return;
    this.loading.set(true);
    this.status.set('Inakagua hatari...');
    this.api.post(`/api/risk/farm/${farm.id}/assess`, {}).subscribe({
      next: () => {
        this.status.set('✅ Ukaguzi umekamilika');
        this.load();
        setTimeout(() => this.status.set(''), 3000);
      },
      error: (e: any) => {
        this.loading.set(false);
        this.status.set('❌ Imeshindwa: ' + e.message);
      },
    });
  }

  sevColor(s: string): string {
    const map: Record<string, string> = {
      CRITICAL: '#b00020', HIGH: '#b00020', MODERATE: '#FF6B35',
      MEDIUM: '#FF6B35', LOW: '#228B22',
    };
    return map[s] ?? '#8B4513';
  }
}
