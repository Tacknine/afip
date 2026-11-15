package tz.afip.farm.repository;
import org.springframework.data.jpa.repository.JpaRepository;
import tz.afip.farm.entity.FarmBoundary;
public interface FarmBoundaryRepository extends JpaRepository<FarmBoundary, Long> { }
