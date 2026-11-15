package tz.afip.ml;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ModelPredictionRepository extends JpaRepository<ModelPrediction, Long> {
    List<ModelPrediction> findByFarmIdOrderByCreatedAtDesc(Long farmId);
}
