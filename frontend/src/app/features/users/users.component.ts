import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { User } from '../../core/models/user.model';

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [CommonModule],
  template: `
    <main>
      <div class="band" style="--b:var(--k);--t:#fff">Watumiaji</div>
      <div class="card">
        @if (loading()) { <div><span class="sp"></span>Inapakia...</div> }
        @else {
          <div class="wrap">
            <table>
              <thead><tr><th>Username</th><th>Roles</th></tr></thead>
              <tbody>
                @for (u of users(); track u.username) {
                  <tr><td>{{ u.username }}</td><td>{{ u.roles.join(', ') }}</td></tr>
                } @empty {
                  <tr><td colspan="2" class="mu">Hakuna watumiaji</td></tr>
                }
              </tbody>
            </table>
          </div>
        }
      </div>
    </main>
  `,
})
export class UsersComponent {
  private api = inject(ApiService);
  users = signal<User[]>([]);
  loading = signal(false);

  constructor() {
    this.loading.set(true);
    this.api.get<User[]>('/api/users').subscribe({
      next: (d) => { this.users.set(d ?? []); this.loading.set(false); },
      error: () => { this.users.set([]); this.loading.set(false); },
    });
  }
}
