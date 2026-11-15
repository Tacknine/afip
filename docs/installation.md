# AFIP — Installation & Deployment Guide

## Quick Start (Development)

```bash
cp .env.example .env
# Edit .env with your credentials
docker compose up --build
cd C:\Users\harun\IdeaProjects\afip
New-Item -ItemType Directory -Force -Path "docs" | Out-Null

$doc = @'
# AFIP — Installation & Deployment Guide

## Quick Start (Development)

1. Copy .env.example to .env
2. Edit .env with your credentials
3. Run: docker compose up --build

## Production

1. Copy .env.example to .env
2. Edit .env with production credentials
3. Run: docker compose -f docker-compose.prod.yml up --build -d

Access: http://localhost

## Services

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80 | Frontend + reverse proxy |
| backend | 8080 | Spring Boot API |
| ml-service | 8000 | Python FastAPI (yield prediction) |
| db | 5432 | PostgreSQL + PostGIS |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/auth/login | POST | Login (JWT) |
| /api/farmers | GET/POST | Farmers |
| /api/farms | GET/POST | Farms |
| /api/farms/{id}/boundary | POST | Set boundary (PostGIS) |
| /api/soil/farm/{id}/fetch | POST | Fetch soil (iSDAsoil) |
| /api/vegetation/farm/{id} | GET | NDVI (NASA) |
| /api/risk/farm/{id}/assess | POST | Assess risks |
| /api/recommendations/farm/{id}/generate | POST | Generate recommendations |
| /api/yield/farm/{id}/predict | POST | Predict yield (ML) |
| /api/reports/farm/{id}/pdf | GET | PDF report |
| /api/reports/farm/{id}/excel | GET | Excel report |

## Environment Variables

See .env.example for all variables.

## Testing

1. Backend tests: docker compose exec backend mvn test
2. ML health: curl http://localhost:8000/health
3. Backend health: curl http://localhost:8080/actuator/health