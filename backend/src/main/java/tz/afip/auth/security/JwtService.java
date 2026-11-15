package tz.afip.auth.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import javax.crypto.SecretKey;
import java.util.Date;

@Service
public class JwtService {
    private final SecretKey key;
    private final long ttlMs;

    public JwtService(@Value("${afip.jwt.secret}") String secret,
                      @Value("${afip.jwt.ttlHours}") long hours) {
        this.key = Keys.hmacShaKeyFor(secret.getBytes());
        this.ttlMs = hours * 3600_000L;
    }

    public String issue(String email, String role) {
        Date now = new Date();
        return Jwts.builder().subject(email).claim("role", role)
            .issuedAt(now).expiration(new Date(now.getTime() + ttlMs))
            .signWith(key).compact();
    }

    public Claims parse(String token) {
        return Jwts.parser().verifyWith(key).build().parseSignedClaims(token).getPayload();
    }
}
