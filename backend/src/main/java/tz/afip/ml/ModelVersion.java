package tz.afip.ml;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.time.Instant;

@Entity
@Table(name = "model_versions")
public class ModelVersion {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "model_name", nullable = false, length = 100)
    private String modelName;

    @Column(nullable = false, length = 30)
    private String version;

    @Column(name = "trained_at")
    private Instant trainedAt;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private JsonNode metrics;

    public Long getId() { return id; }
    public String getModelName() { return modelName; }
    public void setModelName(String v) { this.modelName = v; }
    public String getVersion() { return version; }
    public void setVersion(String v) { this.version = v; }
    public Instant getTrainedAt() { return trainedAt; }
    public void setTrainedAt(Instant v) { this.trainedAt = v; }
    public JsonNode getMetrics() { return metrics; }
    public void setMetrics(JsonNode v) { this.metrics = v; }
}
