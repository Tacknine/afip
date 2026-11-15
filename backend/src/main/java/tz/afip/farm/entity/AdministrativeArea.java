package tz.afip.farm.entity;

import jakarta.persistence.*;
import org.locationtech.jts.geom.MultiPolygon;

@Entity @Table(name = "administrative_areas")
public class AdministrativeArea {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    private String name;
    private String level;
    private String admId;
    @Column(columnDefinition = "geometry(MultiPolygon,4326)") private MultiPolygon geom;
    public Long getId() { return id; }
    public String getName() { return name; }
    public String getAdmId() { return admId; }
    public void setAdmId(String a) { this.admId = a; }
}
