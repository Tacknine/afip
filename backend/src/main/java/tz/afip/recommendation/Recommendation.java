package tz.afip.recommendation;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "recommendations")
public class Recommendation {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "farm_id", nullable = false)
    private Long farmId;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(nullable = false, columnDefinition = "text")
    private String description;

    @Column(nullable = false, columnDefinition = "text")
    private String reason;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "supporting_data", columnDefinition = "jsonb")
    private JsonNode supportingData;

    @Column(nullable = false, length = 20)
    private String priority;

    @Column(precision = 4, scale = 2)
    private BigDecimal confidence;

    @Column(nullable = false, length = 20)
    private String status = "OPEN";

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    public Long getId() { return id; }
    public Long getFarmId() { return farmId; }
    public void setFarmId(Long v) { this.farmId = v; }
    public String getTitle() { return title; }
    public void setTitle(String v) { this.title = v; }
    public String getDescription() { return description; }
    public void setDescription(String v) { this.description = v; }
    public String getReason() { return reason; }
    public void setReason(String v) { this.reason = v; }
    public JsonNode getSupportingData() { return supportingData; }
    public void setSupportingData(JsonNode v) { this.supportingData = v; }
    public String getPriority() { return priority; }
    public void setPriority(String v) { this.priority = v; }
    public BigDecimal getConfidence() { return confidence; }
    public void setConfidence(BigDecimal v) { this.confidence = v; }
    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
    public Instant getCreatedAt() { return createdAt; }
}
