package tz.afip.integration;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ApiSyncLogRepository extends JpaRepository<ApiSyncLog, Long> {
    List<ApiSyncLog> findTop50ByOrderByCreatedAtDesc();
    List<ApiSyncLog> findBySourceCodeOrderByCreatedAtDesc(String sourceCode);
}
