package tz.afip.integration.nasa;

import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import tz.afip.integration.nasa.dto.*;

import java.time.Duration;
import java.util.Base64;

@Component
public class NasaAppearsClient {
    private static final String BASE = "https://appeears.earthdatacloud.nasa.gov/api/";
    private final WebClient wc;

    public NasaAppearsClient() {
        this.wc = WebClient.builder().baseUrl(BASE).build();
    }

    public NasaLoginResponse login(String username, String password) {
        String basic = Base64.getEncoder()
            .encodeToString((username + ":" + password).getBytes());
        return wc.post().uri("login")
            .header("Authorization", "Basic " + basic)
            .retrieve()
            .bodyToMono(NasaLoginResponse.class)
            .block(Duration.ofSeconds(30));
    }

    public NasaTaskSubmitResponse submitTask(String bearer, NasaTaskRequest req) {
        return wc.post().uri("task")
            .header("Authorization", "Bearer " + bearer)
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(req)
            .retrieve()
            .bodyToMono(NasaTaskSubmitResponse.class)
            .block(Duration.ofSeconds(60));
    }

    public NasaTaskStatusResponse taskStatus(String bearer, String taskId) {
        return wc.get().uri("status/{id}", taskId)
            .header("Authorization", "Bearer " + bearer)
            .retrieve()
            .bodyToMono(NasaTaskStatusResponse.class)
            .block(Duration.ofSeconds(30));
    }

    public NasaBundleResponse bundle(String bearer, String taskId) {
        return wc.get().uri("bundle/{id}", taskId)
            .header("Authorization", "Bearer " + bearer)
            .retrieve()
            .bodyToMono(NasaBundleResponse.class)
            .block(Duration.ofSeconds(30));
    }
}
