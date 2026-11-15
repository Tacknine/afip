package tz.afip.integration.isdasoil.dto;

import java.util.List;

public class LayersResponse {
    private List<String> layers;
    private List<String> depths;
    public List<String> getLayers() { return layers; }
    public List<String> getDepths() { return depths; }
}
