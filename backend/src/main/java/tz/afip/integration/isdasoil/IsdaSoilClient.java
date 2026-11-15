package tz.afip.integration.isdasoil;

import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.client.WebClient;
import tz.afip.integration.isdasoil.dto.*;

import java.time.Duration;

@Component
public class IsdaSoilClient {
    private static final String BASE = "https://api.isda-africa.com";
    private final WebClient wc;

    public IsdaSoilClient() {
        this.wc = WebClient.builder().baseUrl(BASE).build();
    }

    public IsdaLoginResponse login(String username, String password) {
        MultiValueMap<String, String> form = new LinkedMultiValueMap<>();
        form.add("username", username);
        form.add("password", password);
        return wc.post().uri("/login")
            .contentType(MediaType.APPLICATION_FORM_URLENCODED)
            .bodyValue(form)
            .retrieve()
            .bodyToMono(IsdaLoginResponse.class)
            .block(Duration.ofSeconds(30));
    }

    public SoilPropertyResponse soilProperty(String bearer, double lat, double lon,
                                             String property, String depth) {
        return wc.get().uri(b -> b.path("/isdasoil/v2/soilproperty")
                .queryParam("lon", lon)
                .queryParam("lat", lat)
                .queryParam("property", property)
                .queryParam("depth", depth)
                .build())
            .header("Authorization", "Bearer " + bearer)
            .accept(MediaType.APPLICATION_JSON)
            .retrieve()
            .bodyToMono(SoilPropertyResponse.class)
            .block(Duration.ofSeconds(30));
    }

    public LayersResponse layers(String bearer) {
        return wc.get().uri("/isdasoil/v2/layers")
            .header("Authorization", "Bearer " + bearer)
            .retrieve()
            .bodyToMono(LayersResponse.class)
            .block(Duration.ofSeconds(30));
    }
}
