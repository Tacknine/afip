package tz.afip.farmer.service;

import org.springframework.stereotype.Service;
import tz.afip.farmer.dto.FarmerRequest;
import tz.afip.farmer.entity.Farmer;
import tz.afip.farmer.repository.FarmerRepository;
import java.util.List;

@Service
public class FarmerService {
    private final FarmerRepository repo;
    public FarmerService(FarmerRepository r) { this.repo = r; }

    public Farmer create(FarmerRequest req) {
        Farmer f = new Farmer();
        f.setFirstName(req.getFirstName());
        f.setLastName(req.getLastName());
        f.setPhone(req.getPhone());
        f.setVillage(req.getVillage());
        f.setDistrict(req.getDistrict());
        f.setRegion(req.getRegion());
        return repo.save(f);
    }

    public List<Farmer> all() { return repo.findAll(); }
}
