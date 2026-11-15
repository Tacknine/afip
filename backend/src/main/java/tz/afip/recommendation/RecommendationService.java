package tz.afip.recommendation;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tz.afip.common.exception.ApiException;
import tz.afip.risk.RiskAssessment;
import tz.afip.risk.RiskAssessmentRepository;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class RecommendationService {

    private final RecommendationRepository repo;
    private final RiskAssessmentRepository riskRepo;

    public RecommendationService(RecommendationRepository repo,
                                RiskAssessmentRepository riskRepo) {
        this.repo = repo;
        this.riskRepo = riskRepo;
    }

    @Transactional
    public List<Recommendation> generateFromRisks(Long farmId) {
        List<RiskAssessment> risks = riskRepo.findByFarmIdOrderByAssessedAtDesc(farmId);
        if (risks.isEmpty()) {
            throw ApiException.badRequest(
                "No risk assessments found for farm " + farmId +
                ". Run /api/risk/farm/{farmId}/assess first.");
        }

        List<Recommendation> results = new ArrayList<>();
        for (RiskAssessment risk : risks) {
            Recommendation r = mapRisk(risk);
            if (r != null) results.add(repo.save(r));
        }
        return results;
    }

    private Recommendation mapRisk(RiskAssessment risk) {
        String category = risk.getRiskCategory();
        String severity = risk.getSeverity();
        JsonNode support = risk.getSupportingData();

        Recommendation r = new Recommendation();
        r.setFarmId(risk.getFarmId());
        r.setConfidence(risk.getConfidence());
        r.setSupportingData(support);
        r.setPriority("HIGH".equals(severity) ? "HIGH"
                    : "MODERATE".equals(severity) ? "MEDIUM" : "LOW");

        switch (category) {
            case "SOIL_ACIDITY":
                r.setTitle("Apply agricultural lime");
                r.setDescription("Soil pH is " + support.path("ph").asText() +
                    " (below 5.5). Lime will raise pH and improve nutrient availability.");
                r.setReason("Acidic soil limits nutrient uptake.");
                break;
            case "LOW_ORGANIC_CARBON":
                r.setTitle("Add compost or manure");
                r.setDescription("Organic carbon is " + support.path("carbon_organic").asText() +
                    " g/kg (below 15). Add compost/manure to improve soil health.");
                r.setReason("Low organic carbon reduces water retention and microbial activity.");
                break;
            case "LOW_NITROGEN":
                r.setTitle("Apply nitrogen fertilizer or legume intercropping");
                r.setDescription("Total nitrogen is " + support.path("nitrogen_total").asText() +
                    " g/kg (below 1.5).");
                r.setReason("Low nitrogen limits crop growth and yield.");
                break;
            case "VEGETATION_STRESS":
                r.setTitle("Inspect crop condition");
                r.setDescription("NDVI is " + support.path("ndvi").asText() +
                    " (below 0.3). Field inspection is recommended.");
                r.setReason("Low NDVI indicates sparse or stressed vegetation.");
                break;
            case "HIGH_CLAY":
                r.setTitle("Improve drainage");
                r.setDescription("Clay content is " + support.path("clay_content").asText() +
                    " % (above 40). Improve drainage to avoid waterlogging.");
                r.setReason("High clay reduces drainage and root penetration.");
                break;
            default:
                return null;
        }
        return r;
    }

    public List<Recommendation> listByFarm(Long farmId) {
        return repo.findByFarmIdOrderByCreatedAtDesc(farmId);
    }
}
