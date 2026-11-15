package tz.afip.farmer.controller;

import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import tz.afip.farmer.dto.*;
import tz.afip.farmer.service.FarmerService;
import java.util.List;

@RestController
@RequestMapping("/api/farmers")
public class FarmerController {
    private final FarmerService service;
    public FarmerController(FarmerService s) { this.service = s; }

    @PostMapping
    @PreAuthorize("hasAnyRole('SUPER_ADMIN','AGRICULTURAL_OFFICER')")
    public ResponseEntity<FarmerResponse> create(@Valid @RequestBody FarmerRequest req) {
        return ResponseEntity.ok(FarmerResponse.from(service.create(req)));
    }

    @GetMapping
    public ResponseEntity<List<FarmerResponse>> list() {
        return ResponseEntity.ok(service.all().stream().map(FarmerResponse::from).toList());
    }
}
