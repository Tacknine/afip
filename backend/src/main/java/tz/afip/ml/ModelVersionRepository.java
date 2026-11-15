package tz.afip.ml;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ModelVersionRepository extends JpaRepository<ModelVersion, Long> {
    Optional<ModelVersion> findByModelNameAndVersion(String modelName, String version);
}
