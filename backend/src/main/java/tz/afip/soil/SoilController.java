package tz.afip.soil;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/soil")
public class SoilController {

    private final SoilService service;
    public SoilController(SoilService s) { this.service = s; }

    @PostMapping("/farm/{farmId}/fetch")
    public ResponseEntity<Map<String, Object>> fetchAndStore(
            @PathVariable Long farmId,
            @RequestParam(defaultValue = "0-20") String depth) {
        List<SoilObservation> obs = service.fetchAndStore(farmId, depth);
        return ResponseEntity.ok(Map.of(
            "farmId", farmId,
            "depth", depth,
            "stored", obs.size(),
            "properties", obs.stream().map(SoilObservation::getProperty).toList()
        ));
    }

    @GetMapping("/farm/{farmId}")
    public ResponseEntity<List<SoilObservation>> list(@PathVariable Long farmId) {
        return ResponseEntity.ok(service.listByFarm(farmId));
    }
}
