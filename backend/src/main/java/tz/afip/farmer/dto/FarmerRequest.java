package tz.afip.farmer.dto;

import jakarta.validation.constraints.NotBlank;

public class FarmerRequest {
    @NotBlank private String firstName;
    @NotBlank private String lastName;
    private String phone;
    private String village;
    private String district;
    private String region;
    public String getFirstName() { return firstName; }
    public void setFirstName(String v) { this.firstName = v; }
    public String getLastName() { return lastName; }
    public void setLastName(String v) { this.lastName = v; }
    public String getPhone() { return phone; }
    public void setPhone(String v) { this.phone = v; }
    public String getVillage() { return village; }
    public void setVillage(String v) { this.village = v; }
    public String getDistrict() { return district; }
    public void setDistrict(String v) { this.district = v; }
    public String getRegion() { return region; }
    public void setRegion(String v) { this.region = v; }
}
