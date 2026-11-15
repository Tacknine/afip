package tz.afip.soil;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface SoilObservationRepository extends JpaRepository<SoilObservation, Long> {
    List<SoilObservation> findByFarmIdOrderByPropertyAsc(Long farmId);
    Optional<SoilObservation> findByFarmIdAndPropertyAndDepthAndSourceCode(
        Long farmId, String property, String depth, String sourceCode);
}
