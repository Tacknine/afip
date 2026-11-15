package tz.afip.integration.nasa.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class NasaTaskRequest {
    @JsonProperty("task_type") private String taskType;
    @JsonProperty("task_name") private String taskName;
    @JsonProperty("params") private Params params;

    public static class Params {
        @JsonProperty("dates") private List<DateRange> dates;
        @JsonProperty("layers") private List<Layer> layers;
        @JsonProperty("coordinates") private List<Coordinate> coordinates;
        public void setDates(List<DateRange> d) { this.dates = d; }
        public void setLayers(List<Layer> l) { this.layers = l; }
        public void setCoordinates(List<Coordinate> c) { this.coordinates = c; }
    }

    public static class DateRange {
        @JsonProperty("startDate") private String startDate;
        @JsonProperty("endDate") private String endDate;
        @JsonProperty("recurring") private Boolean recurring;
        @JsonProperty("yearRange") private int[] yearRange;
        public void setStartDate(String s) { this.startDate = s; }
        public void setEndDate(String s) { this.endDate = s; }
        public void setRecurring(Boolean r) { this.recurring = r; }
        public void setYearRange(int[] y) { this.yearRange = y; }
    }

    public static class Layer {
        @JsonProperty("product") private String product;
        @JsonProperty("layer") private String layer;
        public void setProduct(String p) { this.product = p; }
        public void setLayer(String l) { this.layer = l; }
    }

    public static class Coordinate {
        @JsonProperty("latitude") private double latitude;
        @JsonProperty("longitude") private double longitude;
        @JsonProperty("id") private String id;
        @JsonProperty("category") private String category;
        public void setLatitude(double v) { this.latitude = v; }
        public void setLongitude(double v) { this.longitude = v; }
        public void setId(String v) { this.id = v; }
        public void setCategory(String v) { this.category = v; }
    }

    public void setTaskType(String v) { this.taskType = v; }
    public void setTaskName(String v) { this.taskName = v; }
    public void setParams(Params v) { this.params = v; }
}
