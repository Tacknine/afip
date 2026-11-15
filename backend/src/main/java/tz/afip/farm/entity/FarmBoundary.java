package tz.afip.farm.entity;

import jakarta.persistence.*;
import org.locationtech.jts.geom.Polygon;
import java.time.Instant;

@Entity @Table(name = "farm_boundaries")
public class FarmBoundary {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(nullable = false) private Long farmId;
    @Column(nullable = false, columnDefinition = "geometry(Polygon,4326)") private Polygon geom;
    @Column(nullable = false) private String source = "MANUAL";
    private Instant createdAt = Instant.now();

    public Long getId() { return id; }
    public Long getFarmId() { return farmId; }
    public void setFarmId(Long v) { this.farmId = v; }
    public Polygon getGeom() { return geom; }
    public void setGeom(Polygon v) { this.geom = v; }
    public String getSource() { return source; }
    public void setSource(String v) { this.source = v; }
}
