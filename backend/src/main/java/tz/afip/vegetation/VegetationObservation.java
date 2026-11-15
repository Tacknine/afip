package tz.afip.vegetation;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;

@Entity
@Table(name = "vegetation_observations")
public class VegetationObservation {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "farm_id", nullable = false)
    private Long farmId;

    @Column(name = "source_code", nullable = false, length = 40)
    private String sourceCode;

    @Column(nullable = false, length = 40)
    private String indicator;

    @Column(name = "observed_period", nullable = false, length = 20)
    private String observedPeriod;

    @Column(precision = 8, scale = 4)
    private BigDecimal value;

    @Column(name = "ts_type", length = 20)
    private String tsType;

    @Column(name = "quality_flag", length = 80)
    private String qualityFlag;

    @Column(name = "observed_date")
    private LocalDate observedDate;

    @Column(name = "raw_ref")
    private Long rawRef;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    public Long getId() { return id; }
    public Long getFarmId() { return farmId; }
    public void setFarmId(Long v) { this.farmId = v; }
    public String getSourceCode() { return sourceCode; }
    public void setSourceCode(String v) { this.sourceCode = v; }
    public String getIndicator() { return indicator; }
    public void setIndicator(String v) { this.indicator = v; }
    public String getObservedPeriod() { return observedPeriod; }
    public void setObservedPeriod(String v) { this.observedPeriod = v; }
    public BigDecimal getValue() { return value; }
    public void setValue(BigDecimal v) { this.value = v; }
    public String getTsType() { return tsType; }
    public void setTsType(String v) { this.tsType = v; }
    public String getQualityFlag() { return qualityFlag; }
    public void setQualityFlag(String v) { this.qualityFlag = v; }
    public LocalDate getObservedDate() { return observedDate; }
    public void setObservedDate(LocalDate v) { this.observedDate = v; }
    public Long getRawRef() { return rawRef; }
    public void setRawRef(Long v) { this.rawRef = v; }
    public Instant getCreatedAt() { return createdAt; }
}
