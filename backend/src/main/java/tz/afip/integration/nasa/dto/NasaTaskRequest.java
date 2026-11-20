package tz.afip.integration.nasa.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

public class NasaTaskRequest {

    @JsonProperty("task_type")
    private String taskType;

    @JsonProperty("task_name")
    private String taskName;

    @JsonProperty("params")
    private Params params;

    public static class Params {
        @JsonProperty("dates")
        private List<DateRange> dates;

        @JsonProperty("layers")
        private List<Layer> layers;

        @JsonProperty("coordinates")
        private List<Coordinate> coordinates;

        public void setDates(List<DateRange> d) {
            this.dates = d;
        }

        public void setLayers(List<Layer> l) {
            this.layers = l;
        }

        public void setCoordinates(List<Coordinate> c) {
            this.coordinates = c;
        }
    }

    public static class DateRange {
        @JsonProperty("startDate")
        private String startDate;

        @JsonProperty("endDate")
        private String endDate;

        // Thamani ya msingi ni false ili kuepuka kosa la NASA "None is not of type 'boolean'"
        @JsonProperty("recurring")
        private Boolean recurring = false;

        // Kielezi hiki kinazuia uwanja huu usijumuishwe kwenye JSON wakati ni null,
        // kuepuka kosa la NASA "None is not of type 'array'"
        @JsonProperty("yearRange")
        @JsonInclude(JsonInclude.Include.NON_NULL)
        private int[] yearRange;

        public void setStartDate(String s) {
            this.startDate = s;
        }

        public void setEndDate(String s) {
            this.endDate = s;
        }

        public void setRecurring(Boolean r) {
            this.recurring = r;
        }

        public void setYearRange(int[] y) {
            this.yearRange = y;
        }

        public String getStartDate() {
            return startDate;
        }

        public String getEndDate() {
            return endDate;
        }

        public Boolean getRecurring() {
            return recurring;
        }

        public int[] getYearRange() {
            return yearRange;
        }
    }

    public static class Layer {
        @JsonProperty("product")
        private String product;

        @JsonProperty("layer")
        private String layer;

        public void setProduct(String p) {
            this.product = p;
        }

        public void setLayer(String l) {
            this.layer = l;
        }

        public String getProduct() {
            return product;
        }

        public String getLayer() {
            return layer;
        }
    }

    public static class Coordinate {
        @JsonProperty("latitude")
        private double latitude;

        @JsonProperty("longitude")
        private double longitude;

        @JsonProperty("id")
        private String id;

        @JsonProperty("category")
        private String category;

        public void setLatitude(double v) {
            this.latitude = v;
        }

        public void setLongitude(double v) {
            this.longitude = v;
        }

        public void setId(String v) {
            this.id = v;
        }

        public void setCategory(String v) {
            this.category = v;
        }

        public double getLatitude() {
            return latitude;
        }

        public double getLongitude() {
            return longitude;
        }

        public String getId() {
            return id;
        }

        public String getCategory() {
            return category;
        }
    }

    public void setTaskType(String v) {
        this.taskType = v;
    }

    public void setTaskName(String v) {
        this.taskName = v;
    }

    public void setParams(Params v) {
        this.params = v;
    }

    public String getTaskType() {
        return taskType;
    }

    public String getTaskName() {
        return taskName;
    }

    public Params getParams() {
        return params;
    }
}