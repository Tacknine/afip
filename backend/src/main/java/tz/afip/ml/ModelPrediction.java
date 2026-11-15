package tz.afip.ml;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;

@Entity
@Table(name = "model_predictions")
public class ModelPrediction {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "farm_id", nullable = false)
    private Long farmId;

    @Column(name = "model_version_id", nullable = false)
    private Long modelVersionId;

    @Column(name = "prediction_type", nullable = false, length = 60)
    private String predictionType;

    @Column(precision = 12, scale = 4)
    private BigDecimal value;

    @Column(precision = 4, scale = 2)
    private BigDecimal confidence;

    @Column(name = "predicted_for")
    private LocalDate predictedFor;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private JsonNode inputs;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    public Long getId() { return id; }
    public Long getFarmId() { return farmId; }
    public void setFarmId(Long v) { this.farmId = v; }
    public Long getModelVersionId() { return modelVersionId; }
    public void setModelVersionId(Long v) { this.modelVersionId = v; }
    public String getPredictionType() { return predictionType; }
    public void setPredictionType(String v) { this.predictionType = v; }
    public BigDecimal getValue() { return value; }
    public void setValue(BigDecimal v) { this.value = v; }
    public BigDecimal getConfidence() { return confidence; }
    public void setConfidence(BigDecimal v) { this.confidence = v; }
    public LocalDate getPredictedFor() { return predictedFor; }
    public void setPredictedFor(LocalDate v) { this.predictedFor = v; }
    public JsonNode getInputs() { return inputs; }
    public void setInputs(JsonNode v) { this.inputs = v; }
    public Instant getCreatedAt() { return createdAt; }
}
