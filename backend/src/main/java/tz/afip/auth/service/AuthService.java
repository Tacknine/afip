package tz.afip.auth.service;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tz.afip.auth.dto.*;
import tz.afip.auth.security.JwtService;
import tz.afip.common.exception.ApiException;
import tz.afip.user.entity.*;
import tz.afip.user.repository.*;

@Service
public class AuthService {

    private final UserRepository users;
    private final RoleRepository roles;
    private final PasswordEncoder encoder;
    private final JwtService jwt;
    private final jakarta.persistence.EntityManager em;

    public AuthService(UserRepository u, RoleRepository r, PasswordEncoder e, JwtService j,
                       jakarta.persistence.EntityManager em) {
        this.users = u; this.roles = r; this.encoder = e; this.jwt = j; this.em = em;
    }

    @Transactional
    public void register(RegisterRequest req) {
        if (users.findByEmail(req.getEmail()).isPresent())
            throw ApiException.conflict("Email already registered");

        Role role = roles.findByName(req.getRole())
            .orElseThrow(() -> ApiException.badRequest("Unknown role: " + req.getRole()));

        User u = new User();
        u.setEmail(req.getEmail());
        u.setPasswordHash(encoder.encode(req.getPassword()));
        u.setFullName(req.getFullName());
        users.save(u);

        em.createNativeQuery("INSERT INTO user_roles(user_id, role_id) VALUES (?, ?)")
          .setParameter(1, u.getId()).setParameter(2, role.getId()).executeUpdate();
    }

    public LoginResponse login(LoginRequest req) {
        User u = users.findByEmail(req.getEmail())
            .orElseThrow(() -> ApiException.badRequest("Invalid credentials"));
        if (!encoder.matches(req.getPassword(), u.getPasswordHash()))
            throw ApiException.badRequest("Invalid credentials");

        String role = (String) em.createNativeQuery(
            "SELECT r.name FROM roles r JOIN user_roles ur ON ur.role_id = r.id WHERE ur.user_id = ?")
            .setParameter(1, u.getId()).getResultList().stream().findFirst()
            .orElse("FARMER");

        return new LoginResponse(jwt.issue(u.getEmail(), role));
    }
}
