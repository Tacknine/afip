import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FarmService } from '../../core/services/farm.service';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule],
  template: `
    <main>
      <div class="band" style="--b:var(--fo);--t:#fff">Ripoti</div>
      <div class="card">
        <h2>Pakua ripoti</h2>
        <button class="btn" (click)="download('pdf')">Pakua PDF</button>
        <button class="btn y" (click)="download('excel')">Pakua Excel</button>
        <button class="btn k" style="margin-left:8px" (click)="print()">Chapisha</button>
      </div>
    </main>
  `,
})
export class ReportsComponent {
  farmSvc = inject(FarmService);
  private api = inject(ApiService);

  download(type: 'pdf' | 'excel') {
    const farm = this.farmSvc.selectedFarm();
    if (!farm) return;
    this.api.download(`/api/reports/farm/${farm.id}/${type}`).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `afip-report-${farm.id}.${type === 'pdf' ? 'pdf' : 'xlsx'}`;
        a.click();
        URL.revokeObjectURL(url);
      },
    });
  }

  print() { window.print(); }
}
