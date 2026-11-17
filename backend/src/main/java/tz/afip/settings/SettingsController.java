package tz.afip.settings;

import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/settings")
@PreAuthorize("hasRole('SUPER_ADMIN')")
public class SettingsController {
    private final SettingsService service;

    public SettingsController(SettingsService service) { this.service = service; }

    @GetMapping
    public Map<String, Object> get() { return service.getAll(); }

    @PutMapping
    public ResponseEntity<Void> save(@RequestBody Map<String, Object> body) {
        service.saveAll(body);
        return ResponseEntity.noContent().build();
    }
}