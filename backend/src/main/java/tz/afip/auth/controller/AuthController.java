package tz.afip.auth.controller;

import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import tz.afip.auth.dto.*;
import tz.afip.auth.service.AuthService;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService service;
    public AuthController(AuthService s) { this.service = s; }

    @PostMapping("/register")
    public ResponseEntity<Void> register(@Valid @RequestBody RegisterRequest req) {
        service.register(req);
        return ResponseEntity.accepted().build();
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest req) {
        return ResponseEntity.ok(service.login(req));
    }
}
