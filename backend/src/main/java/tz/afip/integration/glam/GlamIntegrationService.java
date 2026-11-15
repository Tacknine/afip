package tz.afip.integration.glam;

import org.springframework.stereotype.Service;
import tz.afip.integration.ApiSyncLogger;

import java.util.List;

@Service
public class GlamIntegrationService {
    private final GlamClient client;
    private final ApiSyncLogger logger;

    public GlamIntegrationService(GlamClient c, ApiSyncLogger l) {
        this.client = c;
        this.logger = l;
    }

    public String fetch(String sat, String shape, String tsType,
                        List<String> ids, List<Integer> years,
                        String layer, String version, String mask,
                        Integer startMonth, Integer numMonths,
                        Double mcv, String format) {
        // GLAM gettbl/v4 API returns "Table not found" for all IDs
        // Use NASA AppEEARS MOD13Q1.061 for NDVI instead
        throw new IllegalStateException(
            "GLAM gettbl/v4 API is unavailable (returns 400 Table not found). " +
            "This API is deprecated. " +
            "Use NASA AppEEARS MOD13Q1.061 for NDVI data instead.");
    }
}
