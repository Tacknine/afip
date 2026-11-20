package tz.afip.integration.nasa;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.Map;

@RestController
@RequestMapping("/api/integration/nasa")
public class NasaIntegrationController {

    private final NasaAppearsIntegrationService service;

    public NasaIntegrationController(NasaAppearsIntegrationService service) {
        this.service = service;
    }

    /** Starts NASA NDVI download for a farm. Returns 202; poll the status endpoint. */
    @PostMapping("/farm/{farmId}/ndvi")
    public ResponseEntity<Map<String, Object>> start(@PathVariable Long farmId) {
        try {
            return ResponseEntity.accepted().body(service.start(farmId).toMap());
        } catch (IllegalStateException e) {
            String msg = e.getMessage() == null ? "Invalid state" : e.getMessage();
            int code = msg.startsWith("NASA credentials") ? 503 : 400;
            return ResponseEntity.status(code).body(Map.of("message", msg));
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(502).body(Map.of(
                "message", "NASA AppEEARS error " + e.getStatusCode().value() + ": " + e.getResponseBodyAsString()));
        }
    }

    @GetMapping("/farm/{farmId}/ndvi/status")
    public ResponseEntity<Map<String, Object>> status(@PathVariable Long farmId) {
        NasaAppearsIntegrationService.TaskInfo info = service.status(farmId);
        if (info == null) {
            return ResponseEntity.status(404).body(Map.of(
                "status", "NONE",
                "message", "No NASA NDVI task for this farm."));
        }
        return ResponseEntity.ok(info.toMap());
    }
}