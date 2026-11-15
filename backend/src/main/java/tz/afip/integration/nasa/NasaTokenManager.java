package tz.afip.integration.nasa;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import tz.afip.integration.nasa.dto.NasaLoginResponse;

import java.time.Instant;

@Component
public class NasaTokenManager {
    private final NasaAppearsClient client;
    private final String username;
    private final String password;

    private volatile String token;
    private volatile Instant expiry = Instant.EPOCH;

    public NasaTokenManager(NasaAppearsClient client,
                            @Value("${afip.nasa.username:}") String username,
                            @Value("${afip.nasa.password:}") String password) {
        this.client = client;
        this.username = username;
        this.password = password;
    }

    public boolean isConfigured() {
        return username != null && !username.isBlank()
            && password != null && !password.isBlank();
    }

    public synchronized String bearer() {
        if (!isConfigured()) {
            throw new IllegalStateException(
                "NASA credentials not configured. Set AFIP_NASA_USERNAME and AFIP_NASA_PASSWORD.");
        }
        if (token == null || Instant.now().isAfter(expiry.minusSeconds(300))) {
            NasaLoginResponse r = client.login(username, password);
            if (r == null || r.getToken() == null) {
                throw new IllegalStateException("NASA login failed: no token");
            }
            token = r.getToken();
            try {
                expiry = Instant.parse(r.getExpiration());
            } catch (Exception e) {
                expiry = Instant.now().plusSeconds(3600);
            }
        }
        return token;
    }

    public void invalidate() {
        token = null;
        expiry = Instant.EPOCH;
    }
}
