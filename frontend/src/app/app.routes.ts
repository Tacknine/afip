import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./features/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: '',
    loadComponent: () =>
      import('./features/layout/layout.component').then((m) => m.LayoutComponent),
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dash', pathMatch: 'full' },
      { path: 'dash', loadComponent: () => import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent) },
      { path: 'farms', loadComponent: () => import('./features/farms/farms.component').then((m) => m.FarmsComponent) },
      { path: 'soil', loadComponent: () => import('./features/soil/soil.component').then((m) => m.SoilComponent) },
      { path: 'ndvi', loadComponent: () => import('./features/ndvi/ndvi.component').then((m) => m.NdviComponent) },
      { path: 'risk', loadComponent: () => import('./features/risk/risk.component').then((m) => m.RiskComponent) },
      { path: 'rec', loadComponent: () => import('./features/recommendations/recommendations.component').then((m) => m.RecommendationsComponent) },
      { path: 'rotation', loadComponent: () => import('./features/rotation/rotation.component').then((m) => m.RotationComponent) },
      { path: 'nasa', loadComponent: () => import('./features/nasa-data/nasa-data.component').then((m) => m.NasaDataComponent) },
      { path: 'yield', loadComponent: () => import('./features/yield/yield.component').then((m) => m.YieldComponent) },
      { path: 'seed', loadComponent: () => import('./features/seed/seed.component').then((m) => m.SeedComponent) },
      { path: 'notif', loadComponent: () => import('./features/notifications/notifications.component').then((m) => m.NotificationsComponent) },
      { path: 'maps', loadComponent: () => import('./features/maps/maps.component').then((m) => m.MapsComponent) },
      { path: 'rep', loadComponent: () => import('./features/reports/reports.component').then((m) => m.ReportsComponent) },
      { path: 'glossary', loadComponent: () => import('./features/glossary/glossary.component').then((m) => m.GlossaryComponent) },
      { path: 'integ', canActivate: [adminGuard], loadComponent: () => import('./features/integration/integration.component').then((m) => m.IntegrationComponent) },
      { path: 'users', canActivate: [adminGuard], loadComponent: () => import('./features/users/users.component').then((m) => m.UsersComponent) },
      { path: 'settings', canActivate: [adminGuard], loadComponent: () => import('./features/settings/settings.component').then((m) => m.SettingsComponent) },
    ],
  },
  { path: '**', redirectTo: '' },
];
