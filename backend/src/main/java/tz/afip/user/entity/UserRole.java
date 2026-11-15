package tz.afip.user.entity;

import jakarta.persistence.*;
import java.io.Serializable;
import java.util.Objects;

@Entity @Table(name = "user_roles")
@IdClass(UserRole.Key.class)
public class UserRole {
    @Id @Column(name = "user_id") private Long userId;
    @Id @Column(name = "role_id") private Long roleId;

    public UserRole() {}
    public UserRole(Long u, Long r) { this.userId = u; this.roleId = r; }
    public Long getUserId() { return userId; }
    public void setUserId(Long v) { this.userId = v; }
    public Long getRoleId() { return roleId; }
    public void setRoleId(Long v) { this.roleId = v; }

    public static class Key implements Serializable {
        private Long userId;
        private Long roleId;
        @Override public boolean equals(Object o) {
            if (this == o) return true;
            if (!(o instanceof Key k)) return false;
            return Objects.equals(userId, k.userId) && Objects.equals(roleId, k.roleId);
        }
        @Override public int hashCode() { return Objects.hash(userId, roleId); }
    }
}
