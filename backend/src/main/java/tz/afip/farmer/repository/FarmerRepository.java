package tz.afip.farmer.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import tz.afip.farmer.entity.Farmer;

public interface FarmerRepository extends JpaRepository<Farmer, Long> { }
