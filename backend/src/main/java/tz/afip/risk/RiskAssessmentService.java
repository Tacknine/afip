package tz.afip.risk;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tz.afip.common.exception.ApiException;
import tz.afip.farm.entity.Farm;
import tz.afip.farm.repository.FarmRepository;
import tz.afip.soil.SoilObservation;
import tz.afip.soil.SoilObservationRepository;
import tz.afip.vegetation.VegetationObservation;
import tz.afip.vegetation.VegetationObservationRepository;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class RiskAssessmentService {

    private final RiskAssessmentRepository repo;
    private final FarmRepository farms;
    private final SoilObservationRepository soil;
    private final VegetationObservationRepository veg;
    private final ObjectMapper mapper;

    public RiskAssessmentService(RiskAssessmentRepository repo, FarmRepository farms,
                                SoilObservationRepository soil,
                                VegetationObservationRepository veg,
                                ObjectMapper mapper) {
        this.repo = repo;
        this.farms = farms;
        this.soil = soil;
        this.veg = veg;
        this.mapper = mapper;
    }

    @Transactional
    public List<RiskAssessment> assess(Long farmId) {
        Farm farm = farms.findById(farmId)
            .orElseThrow(() -> ApiException.notFound("Farm not found: " + farmId));

        List<SoilObservation> soilObs = soil.findByFarmIdOrderByPropertyAsc(farmId);
        List<VegetationObservation> vegObs = veg.findByFarmIdOrderByObservedDateAsc(farmId);

        Map<String, BigDecimal> soilMap = new LinkedHashMap<>();
        for (SoilObservation s : soilObs) {
            soilMap.put(s.getProperty(), s.getValue());
        }

        BigDecimal latestNdvi = vegObs.isEmpty() ? null
            : vegObs.get(vegObs.size() - 1).getValue();

        List<RiskAssessment> results = new ArrayList<>();

        // Risk 1: Soil pH acidity
        BigDecimal ph = soilMap.get("ph");
        if (ph != null && ph.doubleValue() < 5.5) {
            results.add(build(farmId, "SOIL_ACIDITY",
                ph.doubleValue() < 5.0 ? "HIGH" : "MODERATE",
                BigDecimal.valueOf(0.8),
                Map.of("ph", ph, "threshold", 5.5),
                "Apply agricultural lime to raise soil pH."));
        }

        // Risk 2: Low organic carbon
        BigDecimal carbon = soilMap.get("carbon_organic");
        if (carbon != null && carbon.doubleValue() < 15.0) {
            results.add(build(farmId, "LOW_ORGANIC_CARBON",
                carbon.doubleValue() < 8.0 ? "HIGH" : "MODERATE",
                BigDecimal.valueOf(0.75),
                Map.of("carbon_organic", carbon, "threshold", 15.0),
                "Add compost or manure to improve soil organic matter."));
        }

        // Risk 3: Low nitrogen
        BigDecimal nitrogen = soilMap.get("nitrogen_total");
        if (nitrogen != null && nitrogen.doubleValue() < 1.5) {
            results.add(build(farmId, "LOW_NITROGEN",
                nitrogen.doubleValue() < 1.0 ? "HIGH" : "MODERATE",
                BigDecimal.valueOf(0.7),
                Map.of("nitrogen_total", nitrogen, "threshold", 1.5),
                "Consider nitrogen fertilizer or legume intercropping."));
        }

        // Risk 4: Low NDVI
        if (latestNdvi != null && latestNdvi.doubleValue() < 0.3) {
            results.add(build(farmId, "VEGETATION_STRESS",
                latestNdvi.doubleValue() < 0.2 ? "HIGH" : "MODERATE",
                BigDecimal.valueOf(0.65),
                Map.of("ndvi", latestNdvi, "threshold", 0.3),
                "Inspect crop condition and monitor soil moisture."));
        }

        // Risk 5: High clay
        BigDecimal clay = soilMap.get("clay_content");
        if (clay != null && clay.doubleValue() > 40.0) {
            results.add(build(farmId, "HIGH_CLAY",
                "MODERATE",
                BigDecimal.valueOf(0.6),
                Map.of("clay_content", clay, "threshold", 40.0),
                "Improve drainage and avoid waterlogging."));
        }

        List<RiskAssessment> saved = new ArrayList<>();
        for (RiskAssessment r : results) {
            saved.add(repo.save(r));
        }
        return saved;
    }

    private RiskAssessment build(Long farmId, String category, String severity,
                                BigDecimal confidence, Map<String, Object> data,
                                String action) {
        RiskAssessment r = new RiskAssessment();
        r.setFarmId(farmId);
        r.setRiskCategory(category);
        r.setSeverity(severity);
        r.setConfidence(confidence);
        r.setRecommendedAction(action);
        try {
            r.setSupportingData(mapper.valueToTree(data));
        } catch (Exception e) {
            r.setSupportingData(mapper.createObjectNode());
        }
        return r;
    }

    public List<RiskAssessment> listByFarm(Long farmId) {
        return repo.findByFarmIdOrderByAssessedAtDesc(farmId);
    }
}
