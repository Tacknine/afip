# AFIP frontend API inventory

This inventory was checked against the Java backend controllers and DTOs. The backend is authoritative; endpoint behavior below is not inferred from the previous frontend.

## Frontend architecture

- The deployed UI is the static application in `frontend-static/index.html`, served by Nginx from `docker-compose.prod.yml`. The `frontend/` Angular scaffold is empty and is not part of the current deployment.
- The API client in the page uses one base URL, a bearer token from `sessionStorage`, JSON request bodies, cancellation signals, safe retries for GET requests only, empty `202`/`204` response handling, and status-specific errors.
- The `afip-api-base` meta tag configures the API origin. It defaults to the current origin, which works with the Nginx `/api/` reverse proxy. Do not put credentials in this value.
- `/api/auth/me` is the only success response in this inventory with a `{success,message,data}` wrapper. Other successful endpoints return their declared DTO/entity, arrays, maps, or file bytes directly. Error responses use `{timestamp,status,error,message,path}` where handled by the global exception handler.
- Frontend role checks only adjust visibility and workflow. They are not authorization; backend security must enforce every protected operation.

## Endpoint inventory

| Method and endpoint | Authentication / roles | Request | Actual success response | Frontend use |
|---|---|---|---|---|
| `POST /api/auth/login` | Public | JSON `{email,password}` | `200 {token,tokenType}` (`tokenType: "Bearer"`) | Login |
| `POST /api/auth/register` | Public | JSON `{email,password,fullName,role}`; password minimum 8 characters | `202`, empty body | Registration form |
| `GET /api/auth/me` | Valid JWT required by handler | None | `200 {success:true,message,data:{username,roles:[...]}}`; unauthenticated `401` | Session identity and role |
| `GET /api/farms` | JWT | None | `200` array of `FarmResponse {id,farmerId,name,areaHa}` | Farm search, selection, listing |
| `POST /api/farms` | JWT; `SUPER_ADMIN` or `AGRICULTURAL_OFFICER` | JSON `{farmerId,name}` | `200 FarmResponse {id,farmerId,name,areaHa}` | Farm creation |
| `POST /api/farms/{id}/boundary` | JWT; `SUPER_ADMIN` or `AGRICULTURAL_OFFICER` | JSON `{coordinates:[[x,y],...]}` | `202`, empty body; validates/saves a polygon and updates centroid/area | No boundary editor: farm reads do not return geometry |
| `GET /api/farmers` | JWT | None | `200` array of `FarmerResponse {id,firstName,lastName,phone,village,district,region}` | Farm owner details and farm creation |
| `POST /api/farmers` | JWT; `SUPER_ADMIN` or `AGRICULTURAL_OFFICER` | JSON `{firstName,lastName,phone?,village?,district?,region?}` | `200 FarmerResponse` | Farmer creation |
| `POST /api/soil/farm/{farmId}/fetch` | JWT | Path `farmId`; optional query `depth`, default `"0-20"` | `200 {farmId,depth,stored,properties:[...]}` | Soil fetch |
| `GET /api/soil/farm/{farmId}` | JWT | Path `farmId` | `200` array of `SoilObservation` entities (including property, depth, value, uncertainty and metadata) | Soil indicators and depth history |
| `GET /api/vegetation/farm/{farmId}` | JWT | Path `farmId` | `200` array of `VegetationObservation` entities (including indicator/value/date/source and metadata) | Stored NDVI history |
| `POST /api/vegetation/farm/{farmId}/import-csv` | JWT | Query `csvFilePath` | `200 {farmId,stored,first:{date,ndvi}}` | Not called by the frontend; this server-path import is not a browser file-upload endpoint |
| `GET /api/risk/farm/{farmId}` | JWT | Path `farmId` | `200` array of `RiskAssessment` entities (category, severity, confidence, supporting data, recommended action, timestamp) | Risk cards and dashboard |
| `POST /api/risk/farm/{farmId}/assess` | JWT | Path `farmId` | `200 {farmId,risksFound,risks:[RiskAssessment]}` | Risk assessment |
| `GET /api/yield/farm/{farmId}` | JWT | Path `farmId` | `200` array of `ModelPrediction` entities | Yield history |
| `POST /api/yield/farm/{farmId}/predict` | JWT | Path `farmId` | `200` one `ModelPrediction` entity | Yield prediction |
| `GET /api/recommendations/farm/{farmId}` | JWT | Path `farmId` | `200` array of `Recommendation` entities (title, description, reason, priority, confidence, status, supporting data) | Recommendation cards |
| `POST /api/recommendations/farm/{farmId}/generate` | JWT | Path `farmId` | `200 {farmId,generated,recommendations:[Recommendation]}` | Recommendation generation |
| `GET /api/notifications` | JWT | None | `200` array of `Notification` entities | Notification list and read state |
| `POST /api/notifications/send` | JWT | Query `userId,title,body`; optional `phone` | `200 {id,channel,sentAt}` | Not currently exposed in the UI |
| `POST /api/notifications/{id}/read` | JWT | Path `id` | `200` updated `Notification` entity | Mark notification read |
| `GET /api/reports/farm/{farmId}/pdf` | JWT | Path `farmId` | `200` PDF bytes | Farm PDF download |
| `GET /api/reports/farm/{farmId}/excel` | JWT | Path `farmId` | `200` XLSX bytes | Farm Excel download |
| `GET /api/users` | JWT; `SUPER_ADMIN` | None | `200` array of `{id,email,fullName,role,enabled}` | User listing |
| `PUT /api/users/{id}/role` | JWT; `SUPER_ADMIN`; cannot change own role | JSON `{"role":"SUPER_ADMIN\|AGRICULTURAL_OFFICER\|FARMER\|RESEARCHER\|DATA_ANALYST"}` | `200` one user DTO | Role management |
| `DELETE /api/users/{id}` | JWT; `SUPER_ADMIN`; cannot delete self | Path `id` | `204`, empty body; linked-data conflict is `409` | User deletion |
| `GET /api/settings` | JWT; `SUPER_ADMIN` | None | `200` raw `Map<String,Object>` | Deliberately not called: response may include secrets |
| `PUT /api/settings` | JWT; `SUPER_ADMIN` | JSON arbitrary `Map<String,Object>` | `204`, empty body | Disabled until safe redacted/partial-update contract exists |
| `GET /api/integration/sync-logs` | JWT | None | `200` array of latest 50 `ApiSyncLog` records | Not currently shown |
| `GET /api/integration/health` | JWT | None | `200 {sources:[{code,baseUrl,status,...}]}`; reports NASA AppEEARS, Harvest CKAN and iSDAsoil available, GLAM unavailable | Not currently shown |
| `GET /api/integration/glam/fetch` | JWT | None | `503 {source,status,message,alternative}` | No frontend action; GLAM unavailable |
| `GET /api/integration/isdasoil/status` | JWT | None | `200 {source,baseUrl,configured}` | Not currently shown |
| `GET /api/integration/isdasoil/layers` | JWT | None | `200 LayersResponse`; `503 {message}` if unconfigured | Not currently shown |
| `GET /api/integration/isdasoil/soilproperty` | JWT | Query `lat,lon,property,depth` | `200 SoilPropertyResponse`; `503 {message}` if unconfigured | Not currently shown |

## Verified provider and capability notes

- Yield prediction calls the configured ML service and returns maize yield in tonnes per hectare (`predictionType` is `YIELD_ESTIMATE_MAIZE_T_HA`). `ModelPrediction` includes `id`, `farmId`, `modelVersionId`, `predictionType`, `value`, `confidence`, `predictedFor`, `inputs`, and `createdAt`.
- Notifications have `id`, `userId`, `channel`, `lang`, `title`, `body`, `readAt`, `sentAt`, and `createdAt`. There is no separate status field; `readAt` indicates whether a notification was read. The current GET implementation returns notifications for hard-coded user ID `1`, not necessarily the authenticated user. SMS uses a stub gateway unless Africa's Talking is configured.
- The current backend has no weather route or weather service. The existing frontend optionally queries Open-Meteo directly using farm coordinates; this is a frontend-only external provider and is explicitly identified as such in the UI.
- The frontend's map tiles come from OpenStreetMap and the country outline from a public GeoJSON file. These do not provide farm coordinates. `FarmResponse` contains no coordinates or boundary, so farm markers/boundaries cannot be displayed from the current farm API response.
- There is no backend vegetation `POST .../fetch` route. Stored observations are readable; the backend only offers the server-path CSV import endpoint noted above. The frontend does not call the nonexistent fetch route.
- Farm create and boundary-save operations exist, but no farm update/delete route is present. Farmer list/create exist, but no farmer update/delete route is present.
- User listing, role update, and deletion are in the admin controller. There is no admin-only user-create route: the frontend's add-user form uses the public `POST /api/auth/register` route. The backend must enforce permitted roles and registration policy; hiding the form in the UI is not a security control.
- Settings are an arbitrary map. The current GET can return secrets to the browser and the PUT contract does not describe a safe partial update. The frontend therefore avoids calling GET and disables these controls until the backend provides redacted reads and safe writes.
- iSDAsoil has status/layer/property endpoints. NASA AppEEARS client code exists but no mapped NASA controller endpoint is available; Harvest CKAN has no exposed route; GLAM fetch is explicitly unavailable. `/api/integration/nasa/task` is mentioned only as an alternative string, not an actual route.

## Running the frontend

From the repository root, run `docker compose up --build` and open `http://localhost`. The Nginx container serves `frontend-static/` and proxies `/api/` to the backend. The deployment requires the repository's normal environment configuration; keep all credentials in server-side environment variables, never in the frontend.

For a different deployment origin, set the `afip-api-base` meta tag in `frontend-static/index.html` to the backend origin. An empty value uses the page's origin and is preferred when the reverse proxy is configured.