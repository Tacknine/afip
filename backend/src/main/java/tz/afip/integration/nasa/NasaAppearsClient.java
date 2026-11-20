package tz.afip.integration.nasa;

import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import tz.afip.integration.nasa.dto.*;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
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

    /**
     * Downloads one result file of a finished task to {@code target}.
     * AppEEARS answers with a redirect to a pre-signed S3 URL. That second request
     * must NOT carry the Authorization header (S3 rejects it), so redirects are
     * followed manually.
     */
    public Path downloadFile(String bearer, String taskId, String fileId, Path target) throws IOException {
        HttpClient http = HttpClient.newBuilder()
            .followRedirects(HttpClient.Redirect.NEVER)
            .connectTimeout(Duration.ofSeconds(30))
            .build();
        try {
            HttpRequest first = HttpRequest.newBuilder(URI.create(BASE + "bundle/" + taskId + "/" + fileId))
                .header("Authorization", "Bearer " + bearer)
                .timeout(Duration.ofSeconds(60))
                .GET().build();
            HttpResponse<InputStream> res = http.send(first, HttpResponse.BodyHandlers.ofInputStream());
            int code = res.statusCode();
            if (code >= 300 && code < 400) {
                String location = res.headers().firstValue("Location")
                    .orElseThrow(() -> new IOException("NASA redirect without Location header"));
                res.body().close();
                HttpRequest second = HttpRequest.newBuilder(URI.create(location))
                    .timeout(Duration.ofSeconds(120))
                    .GET().build();
                res = http.send(second, HttpResponse.BodyHandlers.ofInputStream());
                code = res.statusCode();
            }
            if (code != 200) {
                res.body().close();
                throw new IOException("NASA file download failed: HTTP " + code);
            }
            try (InputStream in = res.body()) {
                Files.copy(in, target, StandardCopyOption.REPLACE_EXISTING);
            }
            return target;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IOException("NASA file download interrupted", e);
        }
    }
}