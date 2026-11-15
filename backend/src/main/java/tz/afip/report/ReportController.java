package tz.afip.report;

import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;

@RestController
@RequestMapping("/api/reports")
public class ReportController {

    private final ReportService service;
    public ReportController(ReportService s) { this.service = s; }

    @GetMapping("/farm/{farmId}/pdf")
    public ResponseEntity<byte[]> pdf(@PathVariable Long farmId) throws IOException {
        byte[] data = service.generatePdf(farmId);
        return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION,
                "attachment; filename=farm-" + farmId + "-report.pdf")
            .contentType(MediaType.APPLICATION_PDF)
            .body(data);
    }

    @GetMapping("/farm/{farmId}/excel")
    public ResponseEntity<byte[]> excel(@PathVariable Long farmId) throws IOException {
        byte[] data = service.generateExcel(farmId);
        return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION,
                "attachment; filename=farm-" + farmId + "-report.xlsx")
            .contentType(MediaType.parseMediaType(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
            .body(data);
    }
}
