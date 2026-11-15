package tz.afip.integration;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;

@Service
public class ApiSyncLogger {
    private final ApiSyncLogRepository repo;
    private final ObjectMapper mapper;

    public ApiSyncLogger(ApiSyncLogRepository repo, ObjectMapper mapper) {
        this.repo = repo;
        this.mapper = mapper;
    }

    public ApiSyncLog log(String sourceCode, String endpoint, String method,
                          Integer status, Object request, Object response,
                          boolean success, String error, long durationMs) {
        ApiSyncLog log = new ApiSyncLog();
        log.setSourceCode(sourceCode);
        log.setEndpoint(endpoint);
        log.setHttpMethod(method);
        log.setHttpStatus(status);
        log.setSuccess(success);
        log.setErrorMessage(error);
        log.setDurationMs(durationMs);
        try {
            if (request != null) log.setRequestMeta(mapper.writeValueAsString(request));
            if (response != null) log.setRawResponse(mapper.writeValueAsString(response));
        } catch (Exception e) {
            log.setErrorMessage("Serialization error: " + e.getMessage());
        }
        return repo.save(log);
    }
}
