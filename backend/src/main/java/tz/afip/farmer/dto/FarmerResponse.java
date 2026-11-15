package tz.afip.farmer.dto;

import tz.afip.farmer.entity.Farmer;

public record FarmerResponse(Long id, String firstName, String lastName,
                             String phone, String village, String district, String region) {
    public static FarmerResponse from(Farmer f) {
        return new FarmerResponse(f.getId(), f.getFirstName(), f.getLastName(),
            f.getPhone(), f.getVillage(), f.getDistrict(), f.getRegion());
    }
}
