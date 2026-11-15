package tz.afip.ml;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/yield")
public class YieldController {

    private final YieldPredictionService service;
    public YieldController(YieldPredictionService s) { this.service = s; }

    @PostMapping("/farm/{farmId}/predict")
    public ResponseEntity<ModelPrediction> predict(@PathVariable Long farmId) {
        return ResponseEntity.ok(service.predict(farmId));
    }

    @GetMapping("/farm/{farmId}")
    public ResponseEntity<List<ModelPrediction>> list(@PathVariable Long farmId) {
        return ResponseEntity.ok(service.listByFarm(farmId));
    }
}
