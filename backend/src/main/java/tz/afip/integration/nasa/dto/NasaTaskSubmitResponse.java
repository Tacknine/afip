package tz.afip.integration.nasa.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class NasaTaskSubmitResponse {
    @JsonProperty("task_id") private String taskId;
    @JsonProperty("status") private String status;
    public String getTaskId() { return taskId; }
    public String getStatus() { return status; }
}
