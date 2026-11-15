package tz.afip.integration.isdasoil;

import org.springframework.stereotype.Service;
import tz.afip.integration.ApiSyncLogger;
import tz.afip.integration.isdasoil.dto.*;

@Service
public class IsdaSoilIntegrationService {
    private final IsdaSoilClient client;
    private final IsdaTokenManager tokenManager;
    private final ApiSyncLogger logger;

    public IsdaSoilIntegrationService(IsdaSoilClient c, IsdaTokenManager t, ApiSyncLogger l) {
        this.client = c;
        this.tokenManager = t;
        this.logger = l;
    }

    public boolean isConfigured() {
        return tokenManager.isConfigured();
    }

    public SoilPropertyResponse soilProperty(double lat, double lon, String property, String depth) {
        long start = System.currentTimeMillis();
        try {
            SoilPropertyResponse r = client.soilProperty(
                tokenManager.bearer(), lat, lon, property, depth);
            logger.log("ISDASOIL_V2", "/isdasoil/v2/soilproperty", "GET",
                200, new double[]{lat, lon}, r, true, null,
                System.currentTimeMillis() - start);
            return r;
        } catch (Exception e) {
            logger.log("ISDASOIL_V2", "/isdasoil/v2/soilproperty", "GET",
                null, new double[]{lat, lon}, null, false, e.getMessage(),
                System.currentTimeMillis() - start);
            throw new RuntimeException("iSDAsoil error: " + e.getMessage(), e);
        }
    }

    public LayersResponse layers() {
        long start = System.currentTimeMillis();
        try {
            LayersResponse r = client.layers(tokenManager.bearer());
            logger.log("ISDASOIL_V2", "/isdasoil/v2/layers", "GET",
                200, null, r, true, null,
                System.currentTimeMillis() - start);
            return r;
        } catch (Exception e) {
            logger.log("ISDASOIL_V2", "/isdasoil/v2/layers", "GET",
                null, null, null, false, e.getMessage(),
                System.currentTimeMillis() - start);
            throw new RuntimeException("iSDAsoil error: " + e.getMessage(), e);
        }
    }
}
