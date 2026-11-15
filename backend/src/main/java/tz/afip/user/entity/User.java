package tz.afip.user.entity;

import jakarta.persistence.*;
import java.time.Instant;

@Entity @Table(name = "users")
public class User {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(nullable = false, unique = true) private String email;
    @Column(nullable = false) private String passwordHash;
    @Column(nullable = false) private String fullName;
    private String phone;
    @Column(nullable = false) private String preferredLang = "sw";
    @Column(nullable = false) private boolean enabled = true;
    @Column(nullable = false) private Instant createdAt = Instant.now();
    @Column(nullable = false) private Instant updatedAt = Instant.now();

    public Long getId() { return id; }
    public String getEmail() { return email; }
    public void setEmail(String e) { this.email = e; }
    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String p) { this.passwordHash = p; }
    public String getFullName() { return fullName; }
    public void setFullName(String n) { this.fullName = n; }
    public String getPhone() { return phone; }
    public void setPhone(String p) { this.phone = p; }
    public String getPreferredLang() { return preferredLang; }
    public void setPreferredLang(String l) { this.preferredLang = l; }
    public boolean isEnabled() { return enabled; }
    public void setEnabled(boolean e) { this.enabled = e; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant u) { this.updatedAt = u; }
}
