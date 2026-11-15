package tz.afip.farm.repository;
import org.springframework.data.jpa.repository.JpaRepository;
import tz.afip.farm.entity.Farm;
public interface FarmRepository extends JpaRepository<Farm, Long> { }
