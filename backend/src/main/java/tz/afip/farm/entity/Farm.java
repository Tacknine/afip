package tz.afip.farm.entity;

import jakarta.persistence.*;
import org.locationtech.jts.geom.Point;
import java.math.BigDecimal;
import java.time.Instant;

@Entity @Table(name = "farms")
public class Farm {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(nullable = false) private Long farmerId;
    @Column(nullable = false) private String name;
    private BigDecimal areaHa;
    @Column(columnDefinition = "geography(Point,4326)") private Point centroid;
    private Long adminAreaId;
    private Double latitude;
    private Double longitude;
    private Instant createdAt = Instant.now();
    private Instant updatedAt = Instant.now();

    public Long getId() { return id; }
    public Long getFarmerId() { return farmerId; }
    public void setFarmerId(Long v) { this.farmerId = v; }
    public String getName() { return name; }
    public void setName(String v) { this.name = v; }
    public BigDecimal getAreaHa() { return areaHa; }
    public void setAreaHa(BigDecimal v) { this.areaHa = v; }
    public Point getCentroid() { return centroid; }
    public void setCentroid(Point v) { this.centroid = v; }
    public Long getAdminAreaId() { return adminAreaId; }
    public void setAdminAreaId(Long v) { this.adminAreaId = v; }
    public Double getLatitude() { return latitude; }
    public void setLatitude(Double v) { this.latitude = v; }
    public Double getLongitude() { return longitude; }
    public void setLongitude(Double v) { this.longitude = v; }
}
