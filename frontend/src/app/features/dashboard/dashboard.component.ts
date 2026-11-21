import { Component, inject, effect, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FarmService } from '../../core/services/farm.service';
import { DashboardService } from './dashboard.service';
import { WeatherService } from '../../core/services/weather.service';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { KpiCardComponent } from '../../shared/components/kpi-card.component';
import { NdviGaugeComponent } from '../../shared/components/ndvi-gauge.component';
import { NdviLineComponent } from '../../shared/components/ndvi-line.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, DecimalPipe, FormsModule, KpiCardComponent, NdviGaugeComponent, NdviLineComponent],
  template: `
    <main>
      <div class="search">
        <div class="sbox">
          <input
            type="search"
            placeholder="Tafuta shamba kwa jina, mkoa, au ID..."
            [(ngModel)]="searchQuery"
            (input)="onSearch()"
          />
          @if (showDD() && searchResults().length) {
            <div id="dd" style="display:block">
              @for (f of searchResults(); track f.id) {
                <button (click)="selectFarm(f)">
                  {{ f.name }}
                  <small>ID {{ f.id }}{{ regionOf(f) ? ' - ' + regionOf(f) : '' }}</small>
                </button>
              }
            </div>
          }
        </div>
        <button class="btn y" (click)="onSearch()">Tafuta</button>
      </div>

      @if (!farmSvc.selectedFarm()) {
        <div class="empty">Tafuta shamba ili kuanza</div>
      } @else {
        <div class="hd">
          Shamba: {{ farmSvc.selectedFarm()?.name }} ·
          {{ farmSvc.selectedFarmRegion() || 'mkoa haujatolewa' }} ·
          Farm ID: {{ farmSvc.selectedFarm()?.id }}
        </div>

        @if (dash.loading()) {
          <div><span class="sp"></span>Inapakia data za shamba...</div>
        } @else if (dash.error()) {
          <div class="err">{{ dash.error() }}</div>
        } @else {
          <div class="band" style="--b:var(--g);--t:#000">Muhtasari wa Shamba</div>
          <div class="grid kpis">
            <app-kpi-card label="Wakulima" [value]="farmSvc.farmers().length" color="var(--g)" subtitle="Mfumo wote" />
            <app-kpi-card label="Mashamba" [value]="farmSvc.farms().length" color="var(--y)" subtitle="Mfumo wote" />
            <app-kpi-card label="Hectares" [value]="farmSvc.selectedFarm()?.areaHa ?? '-'" color="var(--k)" subtitle="Shamba hili" />
            <app-kpi-card label="Hatari" [value]="dash.data()?.risk?.length ?? '-'" color="var(--sn)" subtitle="Shamba hili" />
            <app-kpi-card label="Mavuno (t/ha)" [value]="dash.latestYield()?.value ?? '-'" color="var(--sv)" subtitle="Shamba hili" />
            <app-kpi-card label="NDVI" [value]="dash.ndvi()?.value?.toFixed(2) ?? '-'" color="var(--fo)" subtitle="Shamba hili" />
            <app-kpi-card label="Mbegu (kg/ha)" [value]="dash.latestSeed()?.value ?? '-'" color="var(--br)" subtitle="Shamba hili" />
            <app-kpi-card label="Mapendekezo" [value]="dash.data()?.rec?.length ?? '-'" color="var(--br)" subtitle="Shamba hili" />
            <app-kpi-card label="Mvua (mm)" [value]="weatherRain()" color="var(--sk)" subtitle="Siku 30 zilizopita" />
          </div>

          <div class="band" style="--b:var(--fo);--t:#fff">Hali ya Hewa, Uoto na Mavuno</div>
          <div class="grid c3">
            <div class="card">
              <h2>Hali ya hewa</h2>
              @if (weatherTemp() == null && weatherRain() === '-') {
                <p class="mu">Inapakia...</p>
              } @else if (weatherTemp() == null) {
                <p class="mu">{{ weatherRain() }}</p>
              } @else {
                <div class="big">{{ weatherTemp() }}°C</div>
                <p class="mu">Mvua siku 30 zilizopita: {{ weatherRain() }} mm</p>
                <p class="mu">Chanzo: Open-Meteo</p>
              }
            </div>
            <div class="card">
              <h2>NDVI (kipimo cha uoto)</h2>
              <app-ndvi-gauge [value]="dash.ndvi()?.value" [quality]="dash.ndvi()?.qualityFlag ?? ''" />
            </div>
            <div class="card">
              <h2>Mavuno yanayotarajiwa</h2>
              @if (dash.latestYield(); as y) {
                <div class="big">{{ y.value }}</div>
                <p class="mu">t/ha</p>
                <p class="mu">Uhakika: {{ (y.confidence ?? 0) * 100 | number:'1.0-0' }}%</p>
              } @else {
                <p class="mu">Hakuna data</p>
              }
            </div>
          </div>

          <div class="band" style="--b:var(--sv);--t:#000">Uchambuzi wa Data</div>
          <div class="grid c2">
            <div class="card">
              <h2>Udongo (Soil)</h2>
              @if (soilBars().length === 0) {
                <p class="mu">Hakuna data ya udongo</p>
              } @else {
                @for (s of soilBars(); track s.label) {
                  <div class="bar">
                    <span>{{ s.label }}</span>
                    <div><i [style.width.%]="s.pct" [style.--c]="s.color"></i></div>
                    <b>{{ s.value }}{{ s.unit }}</b>
                  </div>
                }
              }
            </div>
            <div class="card">
              <h2>Mwenendo wa NDVI</h2>
              <app-ndvi-line [data]="ndviSeries()" />
            </div>
            <div class="card">
              <h2>Hatari kwa ukali</h2>
              @for (r of riskBars(); track r.label) {
                <div class="bar">
                  <span>{{ r.label }}</span>
                  <div><i [style.width.%]="r.pct" [style.--c]="r.color"></i></div>
                  <b>{{ r.count }}</b>
                </div>
              }
            </div>
          </div>

          <div class="band" style="--b:var(--sk);--t:#000">Mazao na Mbegu</div>
          <div class="grid c2">
            <div class="card">
              <h2>Mazao yanayokadiriwa</h2>
              @if ((dash.data()?.yld ?? []).length === 0) {
                <p class="mu">Hakuna data</p>
              } @else {
                <div class="wrap">
                  <table>
                    <thead><tr><th>Zao</th><th>Mavuno (t/ha)</th><th>Uhakika</th></tr></thead>
                    <tbody>
                      @for (y of dash.data()?.yld; track $index) {
                        <tr>
                          <td>{{ (y.predictionType || '').replace('YIELD_ESTIMATE_','').replace('_T_HA','').toLowerCase() || '-' }}</td>
                          <td><b>{{ y.value }}</b></td>
                          <td>{{ (y.confidence ?? 0) * 100 | number:'1.0-0' }}%</td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              }
            </div>
            <div class="card">
              <h2>Kiasi cha Mbegu</h2>
              @if (dash.latestSeed(); as s) {
                <div class="big">{{ s.value }}</div>
                <p class="mu">kg/ha</p>
                <p class="mu">Uhakika: {{ (s.confidence ?? 0) * 100 | number:'1.0-0' }}%</p>
              } @else {
                <p class="mu">Hakuna data</p>
              }
            </div>
          </div>

          <div class="band" style="--b:var(--k);--t:#fff">Arifa na Vitendo vya Haraka</div>
          <div class="grid c2">
            <div class="card">
              <h2>Arifa za hivi karibuni</h2>
              @if ((dash.data()?.nt ?? []).length === 0) {
                <p class="mu">Hakuna arifa</p>
              } @else {
                <ul>
                  @for (n of (dash.data()?.nt ?? []).slice(0, 5); track n.title) {
                    <li class="it"><b>{{ n.title }}</b><br /><span class="mu">{{ n.body }}</span></li>
                  }
                </ul>
              }
            </div>
            <div class="card">
              <h2>Vitendo vya Haraka</h2>
              <div class="acts">
                <button class="btn" (click)="runAction('soil', 'Fetch Soil', '/api/soil/farm/' + farmSvc.selectedFarm()?.id + '/fetch?depth=0-20')" [disabled]="actionLoading()">Fetch Soil</button>
                <button class="btn o" (click)="runAction('risk', 'Assess Risk', '/api/risk/farm/' + farmSvc.selectedFarm()?.id + '/assess')" [disabled]="actionLoading()">Assess Risk</button>
                <button class="btn k" (click)="runAction('yld', 'Predict Yield', '/api/ml/yield/farm/' + farmSvc.selectedFarm()?.id + '/predict')" [disabled]="actionLoading()">Predict Yield</button>
                <button class="btn y" (click)="runAction('seed', 'Predict Seed', '/api/ml/seed-quantity/farm/' + farmSvc.selectedFarm()?.id + '/predict')" [disabled]="actionLoading()">Predict Seed</button>
                <button class="btn o" (click)="runAction('rec', 'Generate Recs', '/api/recommendations/farm/' + farmSvc.selectedFarm()?.id + '/generate')" [disabled]="actionLoading()">Generate Recs</button>
              </div>
              @if (actionMsg()) {
                <p class="mu" style="margin-top:8px">{{ actionMsg() }}</p>
              }
            </div>
          </div>

          <div class="band" style="--b:var(--sn);--t:#000">Hatari na Mapendekezo</div>
          <div class="grid c2">
            <div class="card">
              <h2>Hatari</h2>
              @if ((dash.data()?.risk ?? []).length === 0) {
                <p class="mu">Hakuna hatari</p>
              } @else {
                <ul>
                  @for (r of dash.data()?.risk; track $index) {
                    <li class="it">
                      <span class="tag" [style.background]="sevColor(r.severity)">{{ r.severity }}</span>
                      <b>{{ (r.riskCategory || '').replace('_',' ') }}</b><br />
                      <span class="mu">{{ r.recommendedAction }}</span>
                    </li>
                  }
                </ul>
              }
            </div>
            <div class="card">
              <h2>Mapendekezo</h2>
              @if ((dash.data()?.rec ?? []).length === 0) {
                <p class="mu">Hakuna mapendekezo</p>
              } @else {
                <ul>
                  @for (r of dash.data()?.rec; track $index) {
                    <li class="it">
                      <span class="tag" [style.background]="prioColor(r.priority)">{{ r.priority }}</span>
                      <b>{{ r.title }}</b><br />
                      <span class="mu">{{ r.description }}</span>
                    </li>
                  }
                </ul>
              }
            </div>
          </div>
        }
      }
    </main>
  `,
})
export class DashboardComponent {
  farmSvc = inject(FarmService);
  dash = inject(DashboardService);
  private weather = inject(WeatherService);
  private api = inject(ApiService);
  auth = inject(AuthService);
  private toast = inject(ToastService);

  searchQuery = '';
  showDD = signal(false);
  searchResults = signal<any[]>([]);
  weatherTemp = signal<number | null>(null);
  weatherRain = signal<string>('-');
  actionLoading = signal(false);
  actionMsg = signal('');

  constructor() {
    effect(() => {
      const farm = this.farmSvc.selectedFarm();
      if (farm) {
        this.dash.load(farm.id);
        this.loadWeather(farm);
      }
    });
  }

  loadWeather(farm: any) {
    const lat = Number(farm.latitude ?? farm.lat);
    const lng = Number(farm.longitude ?? farm.lng ?? farm.lon);
    if (!isFinite(lat) || !isFinite(lng)) {
      this.weatherTemp.set(null);
      this.weatherRain.set('Hakuna viwianishi');
      return;
    }
    this.weather.getCurrent(lat, lng).subscribe({
      next: (j: any) => {
        this.weatherTemp.set(Math.round(j.current?.temperature_2m ?? 0));
        const rain = (j.daily?.precipitation_sum ?? [])
          .slice(0, 30)
          .filter((x: any) => x != null)
          .reduce((a: number, b: number) => a + b, 0);
        this.weatherRain.set(rain.toFixed(0));
      },
      error: () => {
        this.weatherTemp.set(null);
        this.weatherRain.set('-');
      },
    });
  }

  onSearch() {
    const q = this.searchQuery.trim().toLowerCase();
    const results = this.farmSvc.farms().filter((f) => {
      const name = (f.name || '').toLowerCase();
      const region = this.regionOf(f).toLowerCase();
      const farmer = this.farmSvc.farmerName(f).toLowerCase();
      return !q || name.includes(q) || region.includes(q) || farmer.includes(q) || String(f.id) === q;
    });
    this.searchResults.set(results.slice(0, 10));
    this.showDD.set(true);
  }

  selectFarm(f: any) {
    this.searchQuery = f.name || '';
    this.showDD.set(false);
    this.farmSvc.select(f);
  }

  regionOf(f: any): string { return this.farmSvc.regionOf(f); }

  soilBars() {
    const soil = this.dash.data()?.soil ?? [];
    const bars = [
      { label: 'Bulk Density', names: ['bulk_density'], max: 2, color: 'var(--br)', unit: ' g/cm³' },
      { label: 'Clay', names: ['clay_content', 'clay'], max: 100, color: 'var(--br)', unit: '%' },
      { label: 'Sand', names: ['sand_content', 'sand'], max: 100, color: 'var(--sv)', unit: '%' },
      { label: 'Silt', names: ['silt_content', 'silt'], max: 100, color: 'var(--sk)', unit: '%' },
      { label: 'pH', names: ['ph', 'ph_h2o', 'ph_value'], max: 14, color: 'var(--g)', unit: '' },
      { label: 'Nitrogen', names: ['nitrogen_total', 'nitrogen', 'total_nitrogen'], max: 5, color: 'var(--fo)', unit: ' g/kg' },
      { label: 'Carbon', names: ['carbon_organic', 'organic_carbon', 'carbon'], max: 50, color: 'var(--sn)', unit: ' g/kg' },
    ];
    return bars
      .map((b) => {
        const m = soil.find((s: any) => b.names.includes(String(s.property || '').toLowerCase()));
        if (!m) return null;
        const v = Number(m.value);
        return { ...b, value: v, pct: Math.min(100, (v / b.max) * 100) };
      })
      .filter((x): x is any => x != null);
  }

  ndviSeries() {
    return (this.dash.data()?.veg ?? [])
      .filter((v: any) => !v.indicator || v.indicator === 'NDVI')
      .sort((a: any, b: any) => String(this.dash.dateOf(a)).localeCompare(String(this.dash.dateOf(b))))
      .map((v: any) => ({ date: this.dash.dateOf(v), value: v.value }));
  }

  riskBars() {
    const risk = this.dash.data()?.risk ?? [];
    const counts = {
      HIGH: risk.filter((r) => r.severity === 'HIGH' || r.severity === 'CRITICAL').length,
      MEDIUM: risk.filter((r) => r.severity === 'MODERATE' || r.severity === 'MEDIUM').length,
      LOW: risk.filter((r) => r.severity === 'LOW').length,
    };
    const max = Math.max(counts.HIGH, counts.MEDIUM, counts.LOW, 1);
    return [
      { label: 'Juu', count: counts.HIGH, pct: (counts.HIGH / max) * 100, color: '#b00020' },
      { label: 'Wastani', count: counts.MEDIUM, pct: (counts.MEDIUM / max) * 100, color: 'var(--sn)' },
      { label: 'Chini', count: counts.LOW, pct: (counts.LOW / max) * 100, color: 'var(--fo)' },
    ];
  }

  sevColor(s: string): string {
    const map: Record<string, string> = {
      CRITICAL: '#b00020', HIGH: '#b00020', MODERATE: '#FF6B35',
      MEDIUM: '#FF6B35', LOW: '#228B22',
    };
    return map[s] ?? '#8B4513';
  }

  prioColor(p: string): string {
    const map: Record<string, string> = {
      HIGH: '#b00020', MEDIUM: '#FF6B35', LOW: '#228B22',
    };
    return map[p] ?? '#8B4513';
  }

  runAction(_key: string, label: string, path: string) {
    const farm = this.farmSvc.selectedFarm();
    if (!farm) return;
    this.actionLoading.set(true);
    this.actionMsg.set(label + '...');
    this.api.post(path, {}).subscribe({
      next: () => {
        this.actionLoading.set(false);
        this.actionMsg.set('✅ ' + label + ' imekamilika');
        this.dash.load(farm.id);
        setTimeout(() => this.actionMsg.set(''), 3000);
      },
      error: (e: any) => {
        this.actionLoading.set(false);
        this.actionMsg.set('❌ ' + label + ' imeshindwa: ' + e.message);
      },
    });
  }
}



