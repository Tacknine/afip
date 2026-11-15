package tz.afip.integration.isdasoil;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import tz.afip.integration.isdasoil.dto.IsdaLoginResponse;

import java.time.Instant;

@Component
public class IsdaTokenManager {
    private final IsdaSoilClient client;
    private final String username;
    private final String password;

    private volatile String token;
    private volatile Instant expiry = Instant.EPOCH;

    public IsdaTokenManager(IsdaSoilClient client,
                            @Value("${afip.isda.username:}") String username,
                            @Value("${afip.isda.password:}") String password) {
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
                "iSDAsoil credentials not configured. Set AFIP_ISDA_USERNAME and AFIP_ISDA_PASSWORD.");
        }
        if (token == null || Instant.now().isAfter(expiry.minusSeconds(300))) {
            IsdaLoginResponse r = client.login(username, password);
            if (r == null || r.getAccessToken() == null) {
                throw new IllegalStateException("iSDAsoil login failed: no access_token");
            }
            token = r.getAccessToken();
            expiry = Instant.now().plusSeconds(3600);
        }
        return token;
    }

    public void invalidate() {
        token = null;
        expiry = Instant.EPOCH;
    }
}
