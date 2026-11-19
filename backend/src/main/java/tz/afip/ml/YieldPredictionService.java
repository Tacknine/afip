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
import tz.afip.soil.SoilObservation;
import tz.afip.soil.SoilObservationRepository;
import tz.afip.vegetation.VegetationObservation;
import tz.afip.vegetation.VegetationObservationRepository;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class YieldPredictionService {

    private static final Logger log = LoggerFactory.getLogger(YieldPredictionService.class);
    private static final String MODEL_NAME = "yield-ml";
    private static final String MODEL_VERSION = "1.0.0";

    private final FarmRepository farms;
    private final SoilObservationRepository soil;
    private final VegetationObservationRepository veg;
    private final ModelVersionRepository versions;
    private final ModelPredictionRepository predictions;
    private final ObjectMapper mapper;
    private final WebClient mlClient;

    public YieldPredictionService(FarmRepository farms,
                                  SoilObservationRepository soil,
                                  VegetationObservationRepository veg,
                                  ModelVersionRepository versions,
                                  ModelPredictionRepository predictions,
                                  ObjectMapper mapper,
                                  WebClient.Builder webClientBuilder,
                                  @Value("${afip.ml.url:http://localhost:8000}") String mlUrl,
                                  @Value("${afip.ml.connect-timeout-ms:5000}") long connectTimeoutMs,
                                  @Value("${afip.ml.read-timeout-ms:30000}") long readTimeoutMs) {
        this.farms = farms;
        this.soil = soil;
        this.veg = veg;
        this.versions = versions;
        this.predictions = predictions;
        this.mapper = mapper;
        this.mlClient = webClientBuilder
                .baseUrl(mlUrl)
                .clientConnector(new org.springframework.http.client.reactive.ReactorClientHttpConnector(
                        reactor.netty.http.client.HttpClient.create()
                                .option(io.netty.channel.ChannelOption.CONNECT_TIMEOUT_MILLIS, (int) connectTimeoutMs)
                                .responseTimeout(java.time.Duration.ofMillis(readTimeoutMs))))
                .build();
        log.info("YieldPredictionService initialized with ML URL: {} (readTimeout={}ms)", mlUrl, readTimeoutMs);
    }

    @Transactional
    public ModelPrediction predict(Long farmId) {
        log.info("[Yield] predict() called for farm {}", farmId);

        farms.findById(farmId)
            .orElseThrow(() -> ApiException.notFound("Farm not found: " + farmId));

        List<SoilObservation> soilObs = soil.findByFarmIdOrderByPropertyAsc(farmId);
        List<VegetationObservation> vegObs = veg.findByFarmIdOrderByObservedDateAsc(farmId);

        if (soilObs.isEmpty() && vegObs.isEmpty()) {
            throw ApiException.badRequest(
                "No observations for farm " + farmId + ". Fetch soil and NDVI first.");
        }

        Map<String, BigDecimal> soilMap = new LinkedHashMap<>();
        for (SoilObservation s : soilObs) soilMap.put(s.getProperty(), s.getValue());

        BigDecimal latestNdvi = vegObs.isEmpty() ? null
            : vegObs.get(vegObs.size() - 1).getValue();

        Map<String, Object> req = new LinkedHashMap<>();
        req.put("ndvi", latestNdvi != null ? latestNdvi.doubleValue() : 0.3);
        if (soilMap.get("ph") != null) req.put("ph", soilMap.get("ph").doubleValue());
        if (soilMap.get("nitrogen_total") != null) req.put("nitrogen", soilMap.get("nitrogen_total").doubleValue());
        if (soilMap.get("carbon_organic") != null) req.put("carbon", soilMap.get("carbon_organic").doubleValue());

        log.info("[Yield] Calling ML service with: {}", req);

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
            log.error("[Yield] ML service call failed", e);
            throw ApiException.badRequest("ML service unavailable: " + e.getMessage());
        }

        log.info("[Yield] ML response: {}", mlResp);

        if (mlResp == null || mlResp.path("yield_t_ha").isMissingNode()) {
            throw ApiException.badRequest("ML service returned invalid response");
        }

        double yieldValue = mlResp.get("yield_t_ha").asDouble();
        String mlModelVersion = mlResp.path("model_version").asText("1.0.0");
        double confidence = mlResp.path("confidence").asDouble(0.7);

        ModelVersion mv;
        try {
            mv = versions
                .findByModelNameAndVersion(MODEL_NAME, mlModelVersion)
                .orElseGet(() -> {
                    ModelVersion v = new ModelVersion();
                    v.setModelName(MODEL_NAME);
                    v.setVersion(MODEL_VERSION);
                    v.setTrainedAt(Instant.now());
                    try { v.setMetrics(mapper.valueToTree(Map.of(
                        "method", "random-forest-ml", "source", "python-fastapi")));
                    } catch (Exception ex) { log.warn("metrics error: {}", ex.getMessage()); }
                    return versions.save(v);
                });
        } catch (Exception e) {
            log.error("[Yield] Failed to get/save ModelVersion", e);
            throw e;
        }

        log.info("[Yield] ModelVersion id={}", mv.getId());
        log.info("[Yield] Saving prediction: value={}, confidence={}", yieldValue, confidence);

        ModelPrediction p = new ModelPrediction();
        p.setFarmId(farmId);
        p.setModelVersionId(mv.getId());
        p.setPredictionType("YIELD_ESTIMATE_MAIZE_T_HA");
        p.setValue(BigDecimal.valueOf(yieldValue));
        p.setConfidence(BigDecimal.valueOf(confidence));
        p.setPredictedFor(LocalDate.now().plusMonths(4));

        try {
            p.setInputs(mapper.valueToTree(req));
        } catch (Exception e) {
            log.warn("[Yield] inputs conversion error: {}", e.getMessage());
        }

        try {
            ModelPrediction saved = predictions.save(p);
            log.info("[Yield] Saved prediction id={}", saved.getId());
            return saved;
        } catch (Exception e) {
            log.error("[Yield] Failed to save prediction", e);
            throw e;
        }
    }

    public List<ModelPrediction> listByFarm(Long farmId) {
        return predictions.findByFarmIdOrderByCreatedAtDesc(farmId);
    }
}
