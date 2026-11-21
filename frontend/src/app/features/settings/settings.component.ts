import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule],
  template: `
    <main>
      <div class="band" style="--b:var(--br);--t:#fff">Mipangilio</div>
      <div class="card">
        <div class="row">
          <button class="btn" (click)="load()" [disabled]="loading()">Pakia Mipangilio</button>
        </div>
        @if (loading()) { <div><span class="sp"></span>Inapakia...</div> }
        @else {
          <div class="wrap">
            <table>
              <thead><tr><th>Funguo</th><th>Thamani</th></tr></thead>
              <tbody>
                @for (s of settings(); track s.key) {
                  <tr><td>{{ s.key }}</td><td>{{ s.value }}</td></tr>
                } @empty {
                  <tr><td colspan="2" class="mu">Hakuna mipangilio</td></tr>
                }
              </tbody>
            </table>
          </div>
        }
      </div>
    </main>
  `,
})
export class SettingsComponent {
  private api = inject(ApiService);
  settings = signal<{ key: string; value: string }[]>([]);
  loading = signal(false);

  load() {
    this.loading.set(true);
    this.api.get<Record<string, unknown>>('/api/settings').subscribe({
      next: (d) => {
        const arr = Object.entries(d || {}).map(([key, value]) => ({ key, value: String(value) }));
        this.settings.set(arr);
        this.loading.set(false);
      },
      error: () => {
        this.settings.set([]);
        this.loading.set(false);
      },
    });
  }
}
