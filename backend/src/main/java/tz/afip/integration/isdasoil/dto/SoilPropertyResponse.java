package tz.afip.integration.isdasoil.dto;

import com.fasterxml.jackson.databind.JsonNode;

public class SoilPropertyResponse {
    private JsonNode property;

    public JsonNode getProperty() { return property; }
    public void setProperty(JsonNode v) { this.property = v; }
}
