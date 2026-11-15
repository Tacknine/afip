package tz.afip.integration.glam;

import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;
import java.util.List;
import java.util.Map;

@Component
public class GlamClient {
    private static final String BASE = "https://glam1.gsfc.nasa.gov/api/gettbl/v4";
    private final WebClient wc = WebClient.create(BASE);

    public String get(String sat, String shape, String tsType,
                     List<String> ids, List<Integer> years,
                     String layer, String version, String mask,
                     Integer startMonth, Integer numMonths,
                     Double mcv, String format) {
        return wc.get().uri(b -> {
            b.queryParam("sat", sat)
             .queryParam("shape", shape)
             .queryParam("ts_type", tsType);
            if (ids != null) for (String id : ids) b.queryParam("ids", id);
            if (years != null) for (Integer y : years) b.queryParam("years", y);
            if (layer != null) b.queryParam("layer", layer);
            if (version != null) b.queryParam("version", version);
            if (mask != null) b.queryParam("mask", mask);
            if (startMonth != null) b.queryParam("start_month", startMonth);
            if (numMonths != null) b.queryParam("num_months", numMonths);
            if (mcv != null) b.queryParam("mcv", mcv);
            if (format != null) b.queryParam("format", format);
            return b.build();
        }).retrieve()
          .bodyToMono(String.class)
          .block(Duration.ofSeconds(60));
    }

    public String post(Map<String, Object> params) {
        StringBuilder form = new StringBuilder();
        for (Map.Entry<String, Object> e : params.entrySet()) {
            if (e.getValue() instanceof Iterable<?> it) {
                for (Object v : it) {
                    form.append(e.getKey()).append("=").append(v).append("&");
                }
            } else if (e.getValue() != null) {
                form.append(e.getKey()).append("=").append(e.getValue()).append("&");
            }
        }
        return wc.post().contentType(MediaType.APPLICATION_FORM_URLENCODED)
            .bodyValue(form.toString())
            .retrieve()
            .bodyToMono(String.class)
            .block(Duration.ofSeconds(60));
    }
}
