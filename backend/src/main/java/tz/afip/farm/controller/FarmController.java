package tz.afip.farm.controller;

import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import tz.afip.farm.dto.*;
import tz.afip.farm.service.FarmService;
import java.util.List;

@RestController
@RequestMapping("/api/farms")
public class FarmController {

    private final FarmService service;
    public FarmController(FarmService s) { this.service = s; }

    @PostMapping
    @PreAuthorize("hasAnyRole('SUPER_ADMIN','AGRICULTURAL_OFFICER')")
    public ResponseEntity<FarmResponse> create(@Valid @RequestBody FarmRequest req) {
        return ResponseEntity.ok(FarmResponse.from(service.create(req)));
    }

    @PostMapping("/{id}/boundary")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN','AGRICULTURAL_OFFICER')")
    public ResponseEntity<Void> setBoundary(@PathVariable Long id, @RequestBody BoundaryRequest req) {
        service.setBoundary(id, req);
        return ResponseEntity.accepted().build();
    }

    @GetMapping
    public ResponseEntity<List<FarmResponse>> list() {
        return ResponseEntity.ok(service.all().stream().map(FarmResponse::from).toList());
    }
}
