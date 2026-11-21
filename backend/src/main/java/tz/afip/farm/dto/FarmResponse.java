package tz.afip.farm.dto;

import java.math.BigDecimal;
import tz.afip.farm.entity.Farm;

public record FarmResponse(
    Long id,
    Long farmerId,
    String name,
    BigDecimal areaHa,
    Double latitude,
    Double longitude
) {
    public static FarmResponse from(Farm f) {
        return new FarmResponse(
            f.getId(),
            f.getFarmerId(),
            f.getName(),
            f.getAreaHa(),
            f.getLatitude(),
            f.getLongitude()
        );
    }
}
