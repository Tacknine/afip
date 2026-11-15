package tz.afip.integration;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import tz.afip.integration.glam.GlamIntegrationService;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/integration")
public class IntegrationController {

    private final ApiSyncLogRepository logs;
    private final GlamIntegrationService glam;

    public IntegrationController(ApiSyncLogRepository logs,
                                 GlamIntegrationService glam) {
        this.logs = logs;
        this.glam = glam;
    }

    @GetMapping("/sync-logs")
    public ResponseEntity<List<ApiSyncLog>> syncLogs() {
        return ResponseEntity.ok(logs.findTop50ByOrderByCreatedAtDesc());
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
            "sources", List.of(
                Map.of("code", "NASA_APPEARS",
                       "baseUrl", "https://appeears.earthdatacloud.nasa.gov/api/",
                       "status", "available"),
                Map.of("code", "HARVEST_CKAN",
                       "baseUrl", "https://data.harvestportal.org/api/3/action/",
                       "status", "available"),
                Map.of("code", "ISDASOIL_V2",
                       "baseUrl", "https://api.isda-africa.com",
                       "status", "available"),
                Map.of("code", "GLAM_V4",
                       "baseUrl", "https://glam1.gsfc.nasa.gov/api/gettbl/v4",
                       "status", "unavailable",
                       "reason", "HTTP 400 Table not found for all IDs. Use NASA MOD13Q1.061 instead.")
            )
        ));
    }

    @GetMapping("/glam/fetch")
    public ResponseEntity<Map<String, Object>> glamFetch() {
        return ResponseEntity.status(503).body(Map.of(
            "source", "GLAM_V4",
            "status", "unavailable",
            "message", "GLAM gettbl/v4 API is deprecated (returns 400 Table not found). " +
                       "Use NASA AppEEARS MOD13Q1.061 for NDVI data instead.",
            "alternative", Map.of(
                "source", "NASA_APPEARS",
                "product", "MOD13Q1.061",
                "layer", "250m_16_days_NDVI",
                "endpoint", "/api/integration/nasa/task"
            )
        ));
    }
}
