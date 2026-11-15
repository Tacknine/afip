package tz.afip.recommendation;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import tz.afip.notification.NotificationService;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/recommendations")
public class RecommendationController {

    private final RecommendationService service;
    private final NotificationService notifications;

    public RecommendationController(RecommendationService s,
                                   NotificationService n) {
        this.service = s;
        this.notifications = n;
    }

    @PostMapping("/farm/{farmId}/generate")
    public ResponseEntity<Map<String, Object>> generate(@PathVariable Long farmId) {
        List<Recommendation> recs = service.generateFromRisks(farmId);

        // Auto-send notification
        if (!recs.isEmpty()) {
            notifications.sendInApp(1L,
                "Mapendekezo mapya (" + recs.size() + ")",
                "Shamba lako lina mapendekezo " + recs.size() +
                ". Fungua app kuona maelezo.");
        }

        return ResponseEntity.ok(Map.of(
            "farmId", farmId,
            "generated", recs.size(),
            "recommendations", recs
        ));
    }

    @GetMapping("/farm/{farmId}")
    public ResponseEntity<List<Recommendation>> list(@PathVariable Long farmId) {
        return ResponseEntity.ok(service.listByFarm(farmId));
    }
}
