package tz.afip.integration.nasa;

import jakarta.annotation.PreDestroy;
import org.locationtech.jts.geom.Point;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import tz.afip.common.exception.ApiException;
import tz.afip.farm.entity.Farm;
import tz.afip.farm.repository.FarmRepository;
import tz.afip.integration.nasa.dto.NasaBundleResponse;
import tz.afip.integration.nasa.dto.NasaTaskRequest;
import tz.afip.integration.nasa.dto.NasaTaskStatusResponse;
import tz.afip.integration.nasa.dto.NasaTaskSubmitResponse;
import tz.afip.vegetation.VegetationObservation;
import tz.afip.vegetation.VegetationService;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;

/**
 * Pulls NDVI (MOD13Q1.061, 250 m, 16-day) for one farm from NASA AppEEARS:
 * submit point task at the farm centroid -> poll -> download results CSV ->
 * reuse VegetationService.importFromCsv to store the observations.
 *
 * Task state is kept in memory (lost on restart; just start again).
 */
@Service
public class NasaAppearsIntegrationService {

    private static final Logger log = LoggerFactory.getLogger(NasaAppearsIntegrationService.class);

    private static final String PRODUCT = "MOD13Q1.061";
    private static final String NDVI_LAYER = "_250m_16_days_NDVI";
    private static final String QUALITY_LAYER = "_250m_16_days_VI_Quality";
    private static final DateTimeFormatter NASA_DATE = DateTimeFormatter.ofPattern("MM-dd-yyyy");
    private static final Duration MAX_WAIT = Duration.ofMinutes(60);

    private final NasaAppearsClient client;
    private final NasaTokenManager tokens;
    private final FarmRepository farms;
    private final VegetationService vegetation;
    private final int lookbackDays;

    private final Map<Long, TaskInfo> tasks = new ConcurrentHashMap<>();
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1, r -> {
        Thread t = new Thread(r, "nasa-appears-poller");
        t.setDaemon(true);
        return t;
    });

    public NasaAppearsIntegrationService(NasaAppearsClient client,
                                         NasaTokenManager tokens,
                                         FarmRepository farms,
                                         VegetationService vegetation,
                                         @Value("${afip.nasa.lookback-days:365}") int lookbackDays) {
        this.client = client;
        this.tokens = tokens;
        this.farms = farms;
        this.vegetation = vegetation;
        this.lookbackDays = lookbackDays;
    }

    public static final class TaskInfo {
        final Long farmId;
        final String taskId;
        final Instant submittedAt = Instant.now();
        volatile String status = "PENDING";   // PENDING | PROCESSING | IMPORTING | IMPORTED | FAILED
        volatile String message = "Task submitted to NASA AppEEARS.";
        volatile Integer stored;
        volatile int errors;
        volatile ScheduledFuture<?> future;

        TaskInfo(Long farmId, String taskId) {
            this.farmId = farmId;
            this.taskId = taskId;
        }

        boolean isActive() {
            return "PENDING".equals(status) || "PROCESSING".equals(status) || "IMPORTING".equals(status);
        }

        public Map<String, Object> toMap() {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("farmId", farmId);
            m.put("taskId", taskId);
            m.put("status", status);
            m.put("message", message);
            m.put("stored", stored);
            m.put("submittedAt", submittedAt.toString());
            return m;
        }
    }

    /** Starts (or returns the already running) NDVI task for a farm. */
    public synchronized TaskInfo start(Long farmId) {
        TaskInfo existing = tasks.get(farmId);
        if (existing != null && existing.isActive()) return existing;

        if (!tokens.isConfigured()) {
            throw new IllegalStateException(
                "NASA credentials not configured. Set AFIP_NASA_USERNAME and AFIP_NASA_PASSWORD.");
        }
        Farm farm = farms.findById(farmId)
            .orElseThrow(() -> ApiException.notFound("Farm not found: " + farmId));
        Point c = farm.getCentroid();
        if (c == null) {
            throw new IllegalStateException("Farm has no boundary/centroid. Set boundary first.");
        }

        NasaTaskRequest req = buildRequest(farmId, c.getY(), c.getX());
        NasaTaskSubmitResponse resp = withAuth(t -> client.submitTask(t, req));
        if (resp == null || resp.getTaskId() == null) {
            throw new IllegalStateException("NASA did not return a task id.");
        }

        TaskInfo info = new TaskInfo(farmId, resp.getTaskId());
        tasks.put(farmId, info);
        info.future = scheduler.scheduleWithFixedDelay(() -> poll(info), 30, 30, TimeUnit.SECONDS);
        log.info("NASA NDVI task {} submitted for farm {}", info.taskId, farmId);
        return info;
    }

    public TaskInfo status(Long farmId) {
        return tasks.get(farmId);
    }

    private NasaTaskRequest buildRequest(Long farmId, double lat, double lon) {
        LocalDate end = LocalDate.now();
        LocalDate start = end.minusDays(lookbackDays);

        NasaTaskRequest.DateRange range = new NasaTaskRequest.DateRange();
        range.setStartDate(start.format(NASA_DATE));
        range.setEndDate(end.format(NASA_DATE));

        NasaTaskRequest.Layer ndvi = new NasaTaskRequest.Layer();
        ndvi.setProduct(PRODUCT);
        ndvi.setLayer(NDVI_LAYER);

        NasaTaskRequest.Layer quality = new NasaTaskRequest.Layer();
        quality.setProduct(PRODUCT);
        quality.setLayer(QUALITY_LAYER);

        NasaTaskRequest.Coordinate coord = new NasaTaskRequest.Coordinate();
        coord.setLatitude(lat);
        coord.setLongitude(lon);
        coord.setId("farm-" + farmId);
        coord.setCategory("farm");

        NasaTaskRequest.Params params = new NasaTaskRequest.Params();
        params.setDates(List.of(range));
        params.setLayers(List.of(ndvi, quality));
        params.setCoordinates(List.of(coord));

        NasaTaskRequest req = new NasaTaskRequest();
        req.setTaskType("point");
        req.setTaskName("afip-farm-" + farmId + "-" + System.currentTimeMillis());
        req.setParams(params);
        return req;
    }

    private void poll(TaskInfo info) {
        try {
            if (Duration.between(info.submittedAt, Instant.now()).compareTo(MAX_WAIT) > 0) {
                fail(info, "Timed out waiting for NASA (60 minutes).");
                return;
            }
            NasaTaskStatusResponse st = withAuth(t -> client.taskStatus(t, info.taskId));
            String s = (st == null || st.getStatus() == null) ? "" : st.getStatus().toLowerCase();
            switch (s) {
                case "done" -> {
                    info.status = "IMPORTING";
                    info.message = "NASA finished. Importing NDVI...";
                    importResults(info);
                }
                case "error", "failed" -> fail(info, "NASA task failed.");
                case "processing" -> info.status = "PROCESSING";
                default -> { /* pending / unknown: keep waiting */ }
            }
            info.errors = 0;
        } catch (Exception e) {
            log.warn("NASA poll error for farm {}: {}", info.farmId, e.getMessage());
            if (++info.errors >= 5) fail(info, "Repeated errors: " + e.getMessage());
        }
    }

    private void importResults(TaskInfo info) throws Exception {
        NasaBundleResponse bundle = withAuth(t -> client.bundle(t, info.taskId));
        NasaBundleResponse.FileEntry csv = pickCsv(bundle);
        if (csv == null) {
            fail(info, "NASA result has no CSV file.");
            return;
        }
        Path tmp = Files.createTempFile("afip-ndvi-" + info.farmId + "-", ".csv");
        try {
            client.downloadFile(tokens.bearer(), info.taskId, csv.getFileId(), tmp);
            List<VegetationObservation> saved = vegetation.importFromCsv(info.farmId, tmp.toString());
            info.stored = saved.size();
            info.status = "IMPORTED";
            info.message = saved.isEmpty()
                ? "NASA returned no valid NDVI rows for this farm."
                : "NDVI imported.";
            if (info.future != null) info.future.cancel(false);
            log.info("NASA NDVI imported for farm {}: {} rows", info.farmId, saved.size());
        } finally {
            Files.deleteIfExists(tmp);
        }
    }

    private static NasaBundleResponse.FileEntry pickCsv(NasaBundleResponse bundle) {
        if (bundle == null || bundle.getFiles() == null) return null;
        NasaBundleResponse.FileEntry fallback = null;
        for (NasaBundleResponse.FileEntry f : bundle.getFiles()) {
            String name = f.getFileName() == null ? "" : f.getFileName().toLowerCase();
            if (!name.endsWith(".csv") || name.contains("lookup")) continue;
            if (name.contains("results")) return f;
            if (fallback == null) fallback = f;
        }
        return fallback;
    }

    private void fail(TaskInfo info, String message) {
        info.status = "FAILED";
        info.message = message;
        if (info.future != null) info.future.cancel(false);
        log.warn("NASA NDVI task {} for farm {} failed: {}", info.taskId, info.farmId, message);
    }

    /** Runs a NASA call with a bearer token; on 401 refreshes the token once and retries. */
    private <T> T withAuth(Function<String, T> call) {
        try {
            return call.apply(tokens.bearer());
        } catch (WebClientResponseException.Unauthorized e) {
            tokens.invalidate();
            return call.apply(tokens.bearer());
        }
    }

    @PreDestroy
    void shutdown() {
        scheduler.shutdownNow();
    }
}