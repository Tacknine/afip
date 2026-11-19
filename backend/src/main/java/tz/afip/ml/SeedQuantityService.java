package tz.afip.ml;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;
import tz.afip.common.exception.ApiException;
import tz.afip.farm.repository.FarmRepository;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class SeedQuantityService {

    private static final Logger log = LoggerFactory.getLogger(SeedQuantityService.class);
    private static final String MODEL_NAME = "seed_quantity";

    private final FarmRepository farms;
    private final ModelVersionRepository versions;
    private final ModelPredictionRepository predictions;
    private final ObjectMapper mapper;
    private final WebClient mlClient;

    public SeedQuantityService(FarmRepository farms,
                               ModelVersionRepository versions,
                               ModelPredictionRepository predictions,
                               ObjectMapper mapper,
                               WebClient.Builder webClientBuilder,
                               @Value("${afip.ml.url:http://localhost:8000}") String mlUrl,
                               @Value("${afip.ml.connect-timeout-ms:5000}") long connectTimeoutMs,
                               @Value("${afip.ml.read-timeout-ms:30000}") long readTimeoutMs) {
        this.farms = farms;
        this.versions = versions;
        this.predictions = predictions;
        this.mapper = mapper;
        this.mlClient = webClientBuilder
                .baseUrl(mlUrl)
                .clientConnector(new org.springframework.http.client.reactive.ReactorClientHttpConnector(
                        reactor.netty.http.client.HttpClient.create()
                                .option(io.netty.channel.ChannelOption.CONNECT_TIMEOUT_MILLIS, (int) connectTimeoutMs)
                                .responseTimeout(Duration.ofMillis(readTimeoutMs))))
                .build();
        log.info("SeedQuantityService initialized with ML URL: {} (readTimeout={}ms)", mlUrl, readTimeoutMs);
    }

    @Transactional
    public ModelPrediction predict(Long farmId,
                                   Integer cropId,
                                   Double ag4a01, Double ag4a02, Double ag4a04,
                                   Double ag4a06, Double ag4a08) {
        log.info("[SeedQty] predict() called for farm {}", farmId);

        farms.findById(farmId)
            .orElseThrow(() -> ApiException.notFound("Farm not found: " + farmId));

        Map<String, Object> req = new LinkedHashMap<>();
        req.put("cropid", cropId != null ? cropId : 11);
        if (ag4a01 != null) req.put("ag4a_01", ag4a01);
        if (ag4a02 != null) req.put("ag4a_02", ag4a02);
        if (ag4a04 != null) req.put("ag4a_04", ag4a04);
        if (ag4a06 != null) req.put("ag4a_06", ag4a06);
        if (ag4a08 != null) req.put("ag4a_08", ag4a08);

        log.info("[SeedQty] Calling ML service with: {}", req);

        JsonNode mlResp;
        try {
            mlResp = mlClient.post()
                .uri("/predict")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(req)
                .retrieve()
                .bodyToMono(JsonNode.class)
                .block(Duration.ofSeconds(30));
        } catch (Exception e) {
            log.error("[SeedQty] ML service call failed", e);
            throw ApiException.badRequest("ML service unavailable: " + e.getMessage());
        }

        log.info("[SeedQty] ML response: {}", mlResp);

        if (mlResp == null || mlResp.path("seed_quantity_kg").isMissingNode()) {
            throw ApiException.badRequest("ML service returned invalid response");
        }

        double value = mlResp.get("seed_quantity_kg").asDouble();
        String mlModelVersion = mlResp.path("model_version").asText("1.0.0");

        ModelVersion mv = versions
            .findByModelNameAndVersion(MODEL_NAME, mlModelVersion)
            .orElseGet(() -> {
                ModelVersion v = new ModelVersion();
                v.setModelName(MODEL_NAME);
                v.setVersion(mlModelVersion);
                v.setTrainedAt(Instant.now());
                try { v.setMetrics(mapper.valueToTree(Map.of(
                    "method", "random-forest-ml", "source", "python-fastapi")));
                } catch (Exception ex) { log.warn("metrics error: {}", ex.getMessage()); }
                return versions.save(v);
            });

        ModelPrediction p = new ModelPrediction();
        p.setFarmId(farmId);
        p.setModelVersionId(mv.getId());
        p.setPredictionType("SEED_QUANTITY_KG");
        p.setValue(BigDecimal.valueOf(value));
        p.setConfidence(BigDecimal.valueOf(0.7));
        p.setPredictedFor(LocalDate.now().plusMonths(1));

        try {
            p.setInputs(mapper.valueToTree(req));
        } catch (Exception e) {
            log.warn("[SeedQty] inputs conversion error: {}", e.getMessage());
        }

        ModelPrediction saved = predictions.save(p);
        log.info("[SeedQty] Saved prediction id={} value={}", saved.getId(), value);
        return saved;
    }

    public List<ModelPrediction> listByFarm(Long farmId) {
        return predictions.findByFarmIdOrderByCreatedAtDesc(farmId);
    }
}
