package tz.afip.farmer.entity;

import jakarta.persistence.*;
import java.time.Instant;

@Entity @Table(name = "farmers")
public class Farmer {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    private Long userId;
    @Column(nullable = false) private String firstName;
    @Column(nullable = false) private String lastName;
    private String phone;
    private String village;
    private String district;
    private String region;
    private Instant createdAt = Instant.now();
    private Instant updatedAt = Instant.now();

    public Long getId() { return id; }
    public Long getUserId() { return userId; }
    public void setUserId(Long v) { this.userId = v; }
    public String getFirstName() { return firstName; }
    public void setFirstName(String v) { this.firstName = v; }
    public String getLastName() { return lastName; }
    public void setLastName(String v) { this.lastName = v; }
    public String getPhone() { return phone; }
    public void setPhone(String v) { this.phone = v; }
    public String getVillage() { return village; }
    public void setVillage(String v) { this.village = v; }
    public String getDistrict() { return district; }
    public void setDistrict(String v) { this.district = v; }
    public String getRegion() { return region; }
    public void setRegion(String v) { this.region = v; }
}
