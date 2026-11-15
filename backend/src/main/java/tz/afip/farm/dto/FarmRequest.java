package tz.afip.farm.dto;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class FarmRequest {
    @NotNull private Long farmerId;
    @NotBlank private String name;
    public Long getFarmerId() { return farmerId; }
    public void setFarmerId(Long v) { this.farmerId = v; }
    public String getName() { return name; }
    public void setName(String v) { this.name = v; }
}
