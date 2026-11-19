package tz.afip.ml;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/ml")
public class YieldController {

    private final YieldPredictionService yieldService;
    private final SeedQuantityService seedService;

    public YieldController(YieldPredictionService yieldService,
                           SeedQuantityService seedService) {
        this.yieldService = yieldService;
        this.seedService = seedService;
    }

    // ---- Seed Quantity ----

    @PostMapping("/seed-quantity/farm/{farmId}/predict")
    public ResponseEntity<ModelPrediction> predictSeedQuantity(
            @PathVariable Long farmId,
            @RequestBody(required = false) Map<String, Object> body) {
        Integer cropId = body != null && body.get("cropid") != null
                ? ((Number) body.get("cropid")).intValue() : 11;
        return ResponseEntity.ok(seedService.predict(farmId, cropId,
                toDouble(body, "ag4a_01"),
                toDouble(body, "ag4a_02"),
                toDouble(body, "ag4a_04"),
                toDouble(body, "ag4a_06"),
                toDouble(body, "ag4a_08")));
    }

    @GetMapping("/seed-quantity/farm/{farmId}")
    public ResponseEntity<List<ModelPrediction>> listSeedQuantity(@PathVariable Long farmId) {
        return ResponseEntity.ok(seedService.listByFarm(farmId));
    }

    // ---- Yield (legacy, model not trained yet) ----

    @PostMapping("/yield/farm/{farmId}/predict")
    public ResponseEntity<ModelPrediction> predictYield(@PathVariable Long farmId) {
        return ResponseEntity.ok(yieldService.predict(farmId));
    }

    @GetMapping("/yield/farm/{farmId}")
    public ResponseEntity<List<ModelPrediction>> listYield(@PathVariable Long farmId) {
        return ResponseEntity.ok(yieldService.listByFarm(farmId));
    }

    private static Double toDouble(Map<String, Object> body, String key) {
        if (body == null || body.get(key) == null) return null;
        Object v = body.get(key);
        return v instanceof Number ? ((Number) v).doubleValue() : null;
    }
}
