package tz.afip.integration.nasa.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class NasaLoginResponse {
    @JsonProperty("token_type") private String tokenType;
    @JsonProperty("token") private String token;
    @JsonProperty("expiration") private String expiration;
    public String getTokenType() { return tokenType; }
    public String getToken() { return token; }
    public String getExpiration() { return expiration; }
}
