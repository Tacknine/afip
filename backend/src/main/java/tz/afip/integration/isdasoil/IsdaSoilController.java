package tz.afip.integration.isdasoil;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import tz.afip.integration.isdasoil.dto.*;

import java.util.Map;

@RestController
@RequestMapping("/api/integration/isdasoil")
public class IsdaSoilController {
    private final IsdaSoilIntegrationService service;

    public IsdaSoilController(IsdaSoilIntegrationService s) { this.service = s; }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of(
            "source", "ISDASOIL_V2",
            "baseUrl", "https://api.isda-africa.com",
            "configured", service.isConfigured()
        ));
    }

    @GetMapping("/layers")
    public ResponseEntity<?> layers() {
        if (!service.isConfigured()) {
            return ResponseEntity.status(503)
                .body(Map.of("message", "iSDAsoil credentials not configured"));
        }
        return ResponseEntity.ok(service.layers());
    }

    @GetMapping("/soilproperty")
    public ResponseEntity<?> soilProperty(
            @RequestParam double lat,
            @RequestParam double lon,
            @RequestParam String property,
            @RequestParam String depth) {
        if (!service.isConfigured()) {
            return ResponseEntity.status(503)
                .body(Map.of("message", "iSDAsoil credentials not configured"));
        }
        return ResponseEntity.ok(service.soilProperty(lat, lon, property, depth));
    }
}
