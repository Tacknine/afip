package tz.afip.soil;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import com.fasterxml.jackson.databind.JsonNode;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "soil_observations")
public class SoilObservation {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "farm_id", nullable = false)
    private Long farmId;

    @Column(name = "source_code", nullable = false, length = 40)
    private String sourceCode;

    @Column(nullable = false, length = 60)
    private String property;

    @Column(nullable = false, length = 30)
    private String depth;

    @Column(nullable = false, precision = 12, scale = 4)
    private BigDecimal value;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private JsonNode uncertainty;

    @Column(name = "observed_at", nullable = false)
    private Instant observedAt = Instant.now();

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    public Long getId() { return id; }
    public Long getFarmId() { return farmId; }
    public void setFarmId(Long v) { this.farmId = v; }
    public String getSourceCode() { return sourceCode; }
    public void setSourceCode(String v) { this.sourceCode = v; }
    public String getProperty() { return property; }
    public void setProperty(String v) { this.property = v; }
    public String getDepth() { return depth; }
    public void setDepth(String v) { this.depth = v; }
    public BigDecimal getValue() { return value; }
    public void setValue(BigDecimal v) { this.value = v; }
    public JsonNode getUncertainty() { return uncertainty; }
    public void setUncertainty(JsonNode v) { this.uncertainty = v; }
    public Instant getObservedAt() { return observedAt; }
    public void setObservedAt(Instant v) { this.observedAt = v; }
    public Instant getCreatedAt() { return createdAt; }
}

