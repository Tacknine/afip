package tz.afip.report;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class ReportServiceTest {

    @Autowired
    private ReportService service;

    @Test
    void pdfReportShouldNotBeEmpty() throws Exception {
        byte[] pdf = service.generatePdf(3L);
        assertNotNull(pdf);
        assertTrue(pdf.length > 100);
    }

    @Test
    void excelReportShouldNotBeEmpty() throws Exception {
        byte[] xlsx = service.generateExcel(3L);
        assertNotNull(xlsx);
        assertTrue(xlsx.length > 100);
    }
}
