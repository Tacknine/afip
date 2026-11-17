package tz.afip.user.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import tz.afip.user.entity.UserRole;
import java.util.List;

public interface UserRoleRepository extends JpaRepository<UserRole, UserRole.Key> {
    List<UserRole> findByUserId(Long userId);
    void deleteByUserId(Long userId);
}