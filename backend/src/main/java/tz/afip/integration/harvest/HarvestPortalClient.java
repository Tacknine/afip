package tz.afip.integration.harvest;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import tz.afip.integration.harvest.dto.CkanEnvelope;
import tz.afip.integration.harvest.dto.CkanResource;

import java.time.Duration;
import java.util.Map;

@Component
public class HarvestPortalClient {
    private static final String BASE = "https://data.harvestportal.org/api/3/action/";
    private final WebClient wc;
    private final String token;

    public HarvestPortalClient(@Value("${afip.harvest.token:}") String token) {
        this.token = token;
        this.wc = WebClient.builder().baseUrl(BASE).build();
    }

    private WebClient.RequestHeadersSpec<?> auth(WebClient.RequestHeadersSpec<?> spec) {
        if (token != null && !token.isBlank()) {
            spec.header("Authorization", token);
        }
        return spec;
    }

    public CkanEnvelope<CkanResource> resourceShow(String id) {
        return auth(wc.get().uri(b -> b.path("resource_show")
                .queryParam("id", id).build()))
            .retrieve()
            .bodyToMono(new ParameterizedTypeReference<CkanEnvelope<CkanResource>>() {})
            .block(Duration.ofSeconds(30));
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> dataStoreSearch(String resourceId, int limit, int offset, String q) {
        return auth(wc.get().uri(b -> b.path("datastore_search")
                .queryParam("resource_id", resourceId)
                .queryParam("limit", limit)
                .queryParam("offset", offset)
                .queryParam("q", q == null ? "" : q)
                .build()))
            .retrieve()
            .bodyToMono(Map.class)
            .block(Duration.ofSeconds(30));
    }
}
