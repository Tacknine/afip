package tz.afip.notification;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/notifications")
public class NotificationController {

    private final NotificationService service;
    public NotificationController(NotificationService s) { this.service = s; }

    @GetMapping
    public ResponseEntity<List<Notification>> list() {
        Long userId = 1L; // demo: admin user
        return ResponseEntity.ok(service.listByUser(userId));
    }

    @PostMapping("/send")
    public ResponseEntity<Map<String, Object>> send(
            @RequestParam Long userId,
            @RequestParam String title,
            @RequestParam String body,
            @RequestParam(required = false) String phone) {
        Notification n = (phone != null && !phone.isBlank())
            ? service.sendSms(userId, phone, title, body)
            : service.sendInApp(userId, title, body);
        return ResponseEntity.ok(Map.of(
            "id", n.getId(),
            "channel", n.getChannel(),
            "sentAt", n.getSentAt() != null ? n.getSentAt().toString() : "pending"
        ));
    }

    @PostMapping("/{id}/read")
    public ResponseEntity<Notification> markRead(@PathVariable Long id) {
        return ResponseEntity.ok(service.markRead(id));
    }
}
