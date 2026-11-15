package tz.afip.soil;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tz.afip.common.exception.ApiException;
import tz.afip.farm.entity.Farm;
import tz.afip.farm.repository.FarmRepository;
import tz.afip.integration.isdasoil.IsdaSoilIntegrationService;
import tz.afip.integration.isdasoil.dto.SoilPropertyResponse;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Service
public class SoilService {

    private final SoilObservationRepository repo;
    private final FarmRepository farms;
    private final IsdaSoilIntegrationService isda;
    private final ObjectMapper mapper;

    public SoilService(SoilObservationRepository repo, FarmRepository farms,
                       IsdaSoilIntegrationService isda, ObjectMapper mapper) {
        this.repo = repo;
        this.farms = farms;
        this.isda = isda;
        this.mapper = mapper;
    }

    private static final List<String> KEY_PROPERTIES = List.of(
        "clay_content", "sand_content", "silt_content", "ph",
        "nitrogen_total", "carbon_organic", "cation_exchange_capacity",
        "bulk_density", "texture_class"
    );

    @Transactional
    public List<SoilObservation> fetchAndStore(Long farmId, String depth) {
        Farm farm = farms.findById(farmId)
            .orElseThrow(() -> ApiException.notFound("Farm not found: " + farmId));

        if (farm.getCentroid() == null) {
            throw ApiException.badRequest(
                "Farm has no boundary/centroid. Set boundary first.");
        }

        double lat = farm.getCentroid().getY();
        double lon = farm.getCentroid().getX();

        List<SoilObservation> results = new ArrayList<>();
        for (String property : KEY_PROPERTIES) {
            try {
                SoilPropertyResponse r = isda.soilProperty(lat, lon, property, depth);
                SoilObservation obs = parseAndStore(farmId, property, depth, r);
                if (obs != null) results.add(obs);
            } catch (Exception e) {
                // Skip individual property failures
            }
        }
        return results;
    }

    private SoilObservation parseAndStore(Long farmId, String property,
                                         String depth, SoilPropertyResponse r) {
        if (r == null || r.getProperty() == null) return null;

        JsonNode root = r.getProperty();
        JsonNode arr = root.get(property);
        if (arr == null || !arr.isArray() || arr.isEmpty()) return null;

        JsonNode first = arr.get(0);
        JsonNode valueNode = first.path("value").path("value");
        if (valueNode.isMissingNode()) return null;

        BigDecimal value = BigDecimal.valueOf(valueNode.asDouble());

        SoilObservation obs = repo
            .findByFarmIdAndPropertyAndDepthAndSourceCode(
                farmId, property, depth, "ISDASOIL_V2")
            .orElseGet(SoilObservation::new);

        obs.setFarmId(farmId);
        obs.setSourceCode("ISDASOIL_V2");
        obs.setProperty(property);
        obs.setDepth(depth);
        obs.setValue(value);

        try {
            com.fasterxml.jackson.databind.JsonNode uncertainty = first.get("uncertainty");
            obs.setUncertainty(
                uncertainty == null || uncertainty.isNull()
                    ? null
                    : uncertainty
            );
        } catch (Exception e) {
            obs.setUncertainty(null);
        }

        return repo.save(obs);
    }

    public List<SoilObservation> listByFarm(Long farmId) {
        return repo.findByFarmIdOrderByPropertyAsc(farmId);
    }
}
