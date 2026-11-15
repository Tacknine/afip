package tz.afip.vegetation;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/vegetation")
public class VegetationController {

    private final VegetationService service;
    public VegetationController(VegetationService s) { this.service = s; }

    @PostMapping("/farm/{farmId}/import-csv")
    public ResponseEntity<Map<String, Object>> importCsv(
            @PathVariable Long farmId,
            @RequestParam String csvFilePath) {
        List<VegetationObservation> obs = service.importFromCsv(farmId, csvFilePath);
        return ResponseEntity.ok(Map.of(
            "farmId", farmId,
            "stored", obs.size(),
            "first", obs.isEmpty() ? Map.of() : Map.of(
                "date", obs.get(0).getObservedDate(),
                "ndvi", obs.get(0).getValue()
            )
        ));
    }

    @GetMapping("/farm/{farmId}")
    public ResponseEntity<List<VegetationObservation>> list(@PathVariable Long farmId) {
        return ResponseEntity.ok(service.listByFarm(farmId));
    }
}
