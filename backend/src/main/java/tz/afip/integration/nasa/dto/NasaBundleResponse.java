package tz.afip.integration.nasa.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class NasaBundleResponse {
    @JsonProperty("task_id") private String taskId;
    @JsonProperty("files") private List<FileEntry> files;

    public static class FileEntry {
        @JsonProperty("file_id") private String fileId;
        @JsonProperty("file_name") private String fileName;
        @JsonProperty("file_size") private long fileSize;
        @JsonProperty("file_type") private String fileType;
        public String getFileId() { return fileId; }
        public String getFileName() { return fileName; }
        public String getFileType() { return fileType; }
    }

    public String getTaskId() { return taskId; }
    public List<FileEntry> getFiles() { return files; }
}
