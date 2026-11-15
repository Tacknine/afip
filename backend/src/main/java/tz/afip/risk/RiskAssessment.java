package tz.afip.risk;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "risk_assessments")
public class RiskAssessment {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "farm_id", nullable = false)
    private Long farmId;

    @Column(name = "risk_category", nullable = false, length = 60)
    private String riskCategory;

    @Column(nullable = false, length = 20)
    private String severity;

    @Column(precision = 4, scale = 2)
    private BigDecimal confidence;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "supporting_data", columnDefinition = "jsonb")
    private JsonNode supportingData;

    @Column(name = "recommended_action", nullable = false, columnDefinition = "text")
    private String recommendedAction;

    @Column(name = "assessed_at", nullable = false)
    private Instant assessedAt = Instant.now();

    public Long getId() { return id; }
    public Long getFarmId() { return farmId; }
    public void setFarmId(Long v) { this.farmId = v; }
    public String getRiskCategory() { return riskCategory; }
    public void setRiskCategory(String v) { this.riskCategory = v; }
    public String getSeverity() { return severity; }
    public void setSeverity(String v) { this.severity = v; }
    public BigDecimal getConfidence() { return confidence; }
    public void setConfidence(BigDecimal v) { this.confidence = v; }
    public JsonNode getSupportingData() { return supportingData; }
    public void setSupportingData(JsonNode v) { this.supportingData = v; }
    public String getRecommendedAction() { return recommendedAction; }
    public void setRecommendedAction(String v) { this.recommendedAction = v; }
    public Instant getAssessedAt() { return assessedAt; }
}
