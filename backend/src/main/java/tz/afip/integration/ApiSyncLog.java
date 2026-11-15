package tz.afip.integration;

import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.time.Instant;

@Entity
@Table(name = "api_sync_logs")
public class ApiSyncLog {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "source_code", nullable = false, length = 40)
    private String sourceCode;

    @Column(nullable = false, length = 255)
    private String endpoint;

    @Column(name = "http_method", nullable = false, length = 10)
    private String httpMethod;

    @Column(name = "http_status")
    private Integer httpStatus;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "request_meta", columnDefinition = "jsonb")
    private String requestMeta;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "response_meta", columnDefinition = "jsonb")
    private String responseMeta;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "raw_response", columnDefinition = "jsonb")
    private String rawResponse;

    @Column(nullable = false)
    private boolean success;

    @Column(name = "error_message", columnDefinition = "text")
    private String errorMessage;

    @Column(name = "duration_ms")
    private Long durationMs;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    public Long getId() { return id; }
    public String getSourceCode() { return sourceCode; }
    public void setSourceCode(String v) { this.sourceCode = v; }
    public String getEndpoint() { return endpoint; }
    public void setEndpoint(String v) { this.endpoint = v; }
    public String getHttpMethod() { return httpMethod; }
    public void setHttpMethod(String v) { this.httpMethod = v; }
    public Integer getHttpStatus() { return httpStatus; }
    public void setHttpStatus(Integer v) { this.httpStatus = v; }
    public String getRequestMeta() { return requestMeta; }
    public void setRequestMeta(String v) { this.requestMeta = v; }
    public String getResponseMeta() { return responseMeta; }
    public void setResponseMeta(String v) { this.responseMeta = v; }
    public String getRawResponse() { return rawResponse; }
    public void setRawResponse(String v) { this.rawResponse = v; }
    public boolean isSuccess() { return success; }
    public void setSuccess(boolean v) { this.success = v; }
    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String v) { this.errorMessage = v; }
    public Long getDurationMs() { return durationMs; }
    public void setDurationMs(Long v) { this.durationMs = v; }
    public Instant getCreatedAt() { return createdAt; }
}
