package tz.afip.risk;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/risk")
public class RiskController {

    private final RiskAssessmentService service;
    public RiskController(RiskAssessmentService s) { this.service = s; }

    @PostMapping("/farm/{farmId}/assess")
    public ResponseEntity<Map<String, Object>> assess(@PathVariable Long farmId) {
        List<RiskAssessment> risks = service.assess(farmId);
        return ResponseEntity.ok(Map.of(
            "farmId", farmId,
            "risksFound", risks.size(),
            "risks", risks
        ));
    }

    @GetMapping("/farm/{farmId}")
    public ResponseEntity<List<RiskAssessment>> list(@PathVariable Long farmId) {
        return ResponseEntity.ok(service.listByFarm(farmId));
    }
}
