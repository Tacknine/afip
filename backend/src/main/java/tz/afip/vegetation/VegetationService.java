package tz.afip.vegetation;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tz.afip.common.exception.ApiException;
import tz.afip.farm.entity.Farm;
import tz.afip.farm.repository.FarmRepository;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Service
public class VegetationService {

    private final VegetationObservationRepository repo;
    private final FarmRepository farms;
    private final NasaCsvParser parser;

    public VegetationService(VegetationObservationRepository repo,
                            FarmRepository farms,
                            NasaCsvParser parser) {
        this.repo = repo;
        this.farms = farms;
        this.parser = parser;
    }

    @Transactional
    public List<VegetationObservation> importFromCsv(Long farmId, String csvFilePath) {
        Farm farm = farms.findById(farmId)
            .orElseThrow(() -> ApiException.notFound("Farm not found: " + farmId));

        List<VegetationObservation> results = new ArrayList<>();
        try {
            List<NasaCsvParser.Row> rows = parser.parseCsv(csvFilePath);
            for (NasaCsvParser.Row row : rows) {
                if (row.ndvi == null) continue;

                VegetationObservation obs = repo
                    .findByFarmIdAndIndicatorAndObservedDateAndSourceCode(
                        farmId, "NDVI", row.date, "NASA_APPEARS")
                    .orElseGet(VegetationObservation::new);

                obs.setFarmId(farmId);
                obs.setSourceCode("NASA_APPEARS");
                obs.setIndicator("NDVI");
                obs.setObservedDate(row.date);
                obs.setObservedPeriod(row.date.toString());
                obs.setValue(row.ndvi);
                obs.setTsType("historical");
                obs.setQualityFlag(row.modlandDescription != null
                    ? row.modlandDescription
                    : "NDVI");
                results.add(repo.save(obs));
            }
        } catch (Exception e) {
            throw new RuntimeException("CSV parse error: " + e.getMessage(), e);
        }
        return results;
    }

    public List<VegetationObservation> listByFarm(Long farmId) {
        return repo.findByFarmIdOrderByObservedDateAsc(farmId);
    }
}
