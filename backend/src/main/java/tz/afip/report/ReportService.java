package tz.afip.report;

import com.itextpdf.kernel.colors.ColorConstants;
import com.itextpdf.kernel.colors.DeviceRgb;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.layout.Document;
import com.itextpdf.layout.borders.Border;
import com.itextpdf.layout.borders.SolidBorder;
import com.itextpdf.layout.element.Paragraph;
import com.itextpdf.layout.element.Table;
import com.itextpdf.layout.properties.TextAlignment;
import com.itextpdf.layout.properties.UnitValue;
import org.apache.poi.ss.usermodel.CellStyle;
import org.apache.poi.ss.usermodel.FillPatternType;
import org.apache.poi.ss.usermodel.Font;
import org.apache.poi.ss.usermodel.IndexedColors;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.stereotype.Service;
import tz.afip.farm.entity.Farm;
import tz.afip.farm.repository.FarmRepository;
import tz.afip.ml.ModelPrediction;
import tz.afip.ml.ModelPredictionRepository;
import tz.afip.recommendation.Recommendation;
import tz.afip.recommendation.RecommendationRepository;
import tz.afip.risk.RiskAssessment;
import tz.afip.risk.RiskAssessmentRepository;
import tz.afip.soil.SoilObservation;
import tz.afip.soil.SoilObservationRepository;
import tz.afip.vegetation.VegetationObservation;
import tz.afip.vegetation.VegetationObservationRepository;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.time.Instant;
import java.util.List;

@Service
public class ReportService {

    private static final DeviceRgb TANESCO_YELLOW = new DeviceRgb(255, 231, 1);
    private static final DeviceRgb TANESCO_DARK = new DeviceRgb(32, 33, 36);
    private static final DeviceRgb TANESCO_GRAY = new DeviceRgb(240, 240, 240);
    private static final DeviceRgb GREEN = new DeviceRgb(46, 125, 50);
    private static final DeviceRgb AMBER = new DeviceRgb(249, 168, 37);
    private static final DeviceRgb RED = new DeviceRgb(198, 40, 40);

    private final FarmRepository farms;
    private final SoilObservationRepository soil;
    private final VegetationObservationRepository veg;
    private final RiskAssessmentRepository risks;
    private final RecommendationRepository recs;
    private final ModelPredictionRepository predictions;

    public ReportService(FarmRepository farms, SoilObservationRepository soil,
                         VegetationObservationRepository veg,
                         RiskAssessmentRepository risks,
                         RecommendationRepository recs,
                         ModelPredictionRepository predictions) {
        this.farms = farms;
        this.soil = soil;
        this.veg = veg;
        this.risks = risks;
        this.recs = recs;
        this.predictions = predictions;
    }

    public byte[] generatePdf(Long farmId) throws IOException {
        Farm farm = farms.findById(farmId)
            .orElseThrow(() -> new IllegalArgumentException("Farm not found: " + farmId));

        List<SoilObservation> soilObs = soil.findByFarmIdOrderByPropertyAsc(farmId);
        List<VegetationObservation> vegObs = veg.findByFarmIdOrderByObservedDateAsc(farmId);
        List<RiskAssessment> riskList = risks.findByFarmIdOrderByAssessedAtDesc(farmId);
        List<Recommendation> recList = recs.findByFarmIdOrderByCreatedAtDesc(farmId);
        List<ModelPrediction> predList = predictions.findByFarmIdOrderByCreatedAtDesc(farmId);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        PdfWriter writer = new PdfWriter(baos);
        PdfDocument pdf = new PdfDocument(writer);
        Document doc = new Document(pdf);

        // === HEADER (TANESCO style) ===
        Table header = new Table(UnitValue.createPercentArray(new float[]{1})).useAllAvailableWidth();
        com.itextpdf.layout.element.Cell headerCell = new com.itextpdf.layout.element.Cell()
            .setBackgroundColor(TANESCO_DARK)
            .setPadding(20).setBorder(Border.NO_BORDER);
        headerCell.add(new Paragraph("AFIP").setFontSize(28).setBold().setFontColor(TANESCO_YELLOW));
        headerCell.add(new Paragraph("Farm Assessment Report").setFontSize(16).setFontColor(ColorConstants.WHITE));
        headerCell.add(new Paragraph("Shamba: " + farm.getName() + " (ID: " + farm.getId() + ")")
            .setFontSize(12).setFontColor(TANESCO_YELLOW));
        header.addCell(headerCell);
        doc.add(header);

        doc.add(new Paragraph("\\n"));

        // === FARM DETAILS ===
        Table farmTable = new Table(UnitValue.createPercentArray(new float[]{1, 2})).useAllAvailableWidth();
        farmTable.addCell(new com.itextpdf.layout.element.Cell().setBackgroundColor(TANESCO_GRAY)
            .add(new Paragraph("Eneo (ha)").setBold()));
        farmTable.addCell(new com.itextpdf.layout.element.Cell()
            .add(new Paragraph(farm.getAreaHa() != null ? farm.getAreaHa().toString() : "N/A")));
        farmTable.addCell(new com.itextpdf.layout.element.Cell().setBackgroundColor(TANESCO_GRAY)
            .add(new Paragraph("Tarehe").setBold()));
        farmTable.addCell(new com.itextpdf.layout.element.Cell()
            .add(new Paragraph(Instant.now().toString())));
        doc.add(farmTable);
        doc.add(new Paragraph("\\n"));

        // === SOIL ===
        if (!soilObs.isEmpty()) {
            doc.add(sectionHeader("SOIL PROPERTIES (0-20cm)", GREEN));
            Table t = new Table(UnitValue.createPercentArray(new float[]{3, 2, 2})).useAllAvailableWidth();
            addTableHeader(t, new String[]{"Property", "Value", "Depth"}, GREEN);
            for (SoilObservation s : soilObs) {
                t.addCell(new com.itextpdf.layout.element.Cell()
                    .add(new Paragraph(s.getProperty().replace("_", " "))));
                t.addCell(new com.itextpdf.layout.element.Cell()
                    .add(new Paragraph(s.getValue() != null ? s.getValue().toString() : "N/A")));
                t.addCell(new com.itextpdf.layout.element.Cell()
                    .add(new Paragraph(s.getDepth())));
            }
            doc.add(t);
            doc.add(new Paragraph("\\n"));
        }

        // === NDVI ===
        if (!vegObs.isEmpty()) {
            doc.add(sectionHeader("VEGETATION (NDVI)", GREEN));
            Table t = new Table(UnitValue.createPercentArray(new float[]{2, 2})).useAllAvailableWidth();
            addTableHeader(t, new String[]{"Date", "NDVI"}, GREEN);
            for (VegetationObservation v : vegObs) {
                t.addCell(new com.itextpdf.layout.element.Cell()
                    .add(new Paragraph(v.getObservedDate().toString())));
                t.addCell(new com.itextpdf.layout.element.Cell()
                    .add(new Paragraph(v.getValue().toString())));
            }
            doc.add(t);
            doc.add(new Paragraph("\\n"));
        }

        // === YIELD ===
        if (!predList.isEmpty()) {
            ModelPrediction p = predList.get(0);
            doc.add(sectionHeader("YIELD PREDICTION", GREEN));
            Table t = new Table(UnitValue.createPercentArray(new float[]{1, 1})).useAllAvailableWidth();
            t.addCell(new com.itextpdf.layout.element.Cell().setBackgroundColor(TANESCO_GRAY)
                .add(new Paragraph("Mavuno (t/ha)").setBold()));
            t.addCell(new com.itextpdf.layout.element.Cell()
                .add(new Paragraph(p.getValue().toString()).setFontSize(20).setBold().setFontColor(GREEN)));
            t.addCell(new com.itextpdf.layout.element.Cell().setBackgroundColor(TANESCO_GRAY)
                .add(new Paragraph("Confidence").setBold()));
            t.addCell(new com.itextpdf.layout.element.Cell()
                .add(new Paragraph((p.getConfidence().doubleValue() * 100) + "%")));
            doc.add(t);
            doc.add(new Paragraph("\\n"));
        }

        // === RISKS ===
        if (!riskList.isEmpty()) {
            doc.add(sectionHeader("RISK ASSESSMENT", AMBER));
            Table t = new Table(UnitValue.createPercentArray(new float[]{2, 1, 4})).useAllAvailableWidth();
            addTableHeader(t, new String[]{"Category", "Severity", "Action"}, AMBER);
            for (RiskAssessment r : riskList) {
                DeviceRgb sevColor = r.getSeverity().equals("HIGH") ? RED
                    : r.getSeverity().equals("MODERATE") ? AMBER : GREEN;
                t.addCell(new com.itextpdf.layout.element.Cell()
                    .add(new Paragraph(r.getRiskCategory().replace("_", " "))));
                t.addCell(new com.itextpdf.layout.element.Cell().setBackgroundColor(sevColor)
                    .add(new Paragraph(r.getSeverity()).setFontColor(ColorConstants.WHITE).setBold()));
                t.addCell(new com.itextpdf.layout.element.Cell()
                    .add(new Paragraph(r.getRecommendedAction())));
            }
            doc.add(t);
            doc.add(new Paragraph("\\n"));
        }

        // === RECOMMENDATIONS ===
        if (!recList.isEmpty()) {
            doc.add(sectionHeader("RECOMMENDATIONS", GREEN));
            for (Recommendation r : recList) {
                Table t = new Table(UnitValue.createPercentArray(new float[]{1})).useAllAvailableWidth();
                com.itextpdf.layout.element.Cell c = new com.itextpdf.layout.element.Cell()
                    .setBorder(new SolidBorder(GREEN, 1)).setPadding(10);
                c.add(new Paragraph("[" + r.getPriority() + "] " + r.getTitle()).setBold());
                c.add(new Paragraph("Reason: " + r.getReason()).setFontSize(10));
                t.addCell(c);
                doc.add(t);
            }
        }

        doc.close();
        return baos.toByteArray();
    }

    private Paragraph sectionHeader(String text, DeviceRgb color) {
        return new Paragraph(text).setFontSize(14).setBold()
            .setFontColor(ColorConstants.WHITE).setBackgroundColor(color)
            .setPadding(8).setMarginTop(10);
    }

    private void addTableHeader(Table t, String[] headers, DeviceRgb color) {
        for (String h : headers) {
            t.addHeaderCell(new com.itextpdf.layout.element.Cell().setBackgroundColor(color)
                .add(new Paragraph(h).setFontColor(ColorConstants.WHITE).setBold()));
        }
    }

    public byte[] generateExcel(Long farmId) throws IOException {
        Farm farm = farms.findById(farmId)
            .orElseThrow(() -> new IllegalArgumentException("Farm not found: " + farmId));

        List<SoilObservation> soilObs = soil.findByFarmIdOrderByPropertyAsc(farmId);
        List<VegetationObservation> vegObs = veg.findByFarmIdOrderByObservedDateAsc(farmId);
        List<RiskAssessment> riskList = risks.findByFarmIdOrderByAssessedAtDesc(farmId);
        List<Recommendation> recList = recs.findByFarmIdOrderByCreatedAtDesc(farmId);

        try (XSSFWorkbook wb = new XSSFWorkbook();
             ByteArrayOutputStream baos = new ByteArrayOutputStream()) {

            CellStyle headerStyle = wb.createCellStyle();
            headerStyle.setFillForegroundColor(IndexedColors.DARK_TEAL.getIndex());
            headerStyle.setFillPattern(FillPatternType.SOLID_FOREGROUND);
            Font headerFont = wb.createFont();
            headerFont.setColor(IndexedColors.WHITE.getIndex());
            headerFont.setBold(true);
            headerStyle.setFont(headerFont);

            Sheet s1 = wb.createSheet("Farm Info");
            Row r0 = s1.createRow(0); r0.createCell(0).setCellValue("Farm Name"); r0.createCell(1).setCellValue(farm.getName());
            Row r1 = s1.createRow(1); r1.createCell(0).setCellValue("Farm ID"); r1.createCell(1).setCellValue(farm.getId());

            Sheet s2 = wb.createSheet("Soil");
            Row h2 = s2.createRow(0);
            String[] soilHeaders = {"Property", "Value", "Depth"};
            for (int i = 0; i < soilHeaders.length; i++) {
                org.apache.poi.ss.usermodel.Cell cell = h2.createCell(i);
                cell.setCellValue(soilHeaders[i]); cell.setCellStyle(headerStyle);
            }
            int rn = 1;
            for (SoilObservation s : soilObs) {
                Row row = s2.createRow(rn++);
                row.createCell(0).setCellValue(s.getProperty());
                row.createCell(1).setCellValue(s.getValue() != null ? s.getValue().doubleValue() : 0);
                row.createCell(2).setCellValue(s.getDepth());
            }

            Sheet s3 = wb.createSheet("NDVI");
            Row h3 = s3.createRow(0);
            h3.createCell(0).setCellValue("Date"); h3.createCell(1).setCellValue("NDVI");
            h3.getCell(0).setCellStyle(headerStyle); h3.getCell(1).setCellStyle(headerStyle);
            int r3 = 1;
            for (VegetationObservation v : vegObs) {
                Row row = s3.createRow(r3++);
                row.createCell(0).setCellValue(v.getObservedDate().toString());
                row.createCell(1).setCellValue(v.getValue().doubleValue());
            }

            Sheet s4 = wb.createSheet("Risks");
            Row h4 = s4.createRow(0);
            String[] riskHeaders = {"Category", "Severity", "Action"};
            for (int i = 0; i < riskHeaders.length; i++) {
                org.apache.poi.ss.usermodel.Cell cell = h4.createCell(i);
                cell.setCellValue(riskHeaders[i]); cell.setCellStyle(headerStyle);
            }
            int r4 = 1;
            for (RiskAssessment r : riskList) {
                Row row = s4.createRow(r4++);
                row.createCell(0).setCellValue(r.getRiskCategory());
                row.createCell(1).setCellValue(r.getSeverity());
                row.createCell(2).setCellValue(r.getRecommendedAction());
            }

            Sheet s5 = wb.createSheet("Recommendations");
            Row h5 = s5.createRow(0);
            String[] recHeaders = {"Title", "Priority", "Reason"};
            for (int i = 0; i < recHeaders.length; i++) {
                org.apache.poi.ss.usermodel.Cell cell = h5.createCell(i);
                cell.setCellValue(recHeaders[i]); cell.setCellStyle(headerStyle);
            }
            int r5 = 1;
            for (Recommendation r : recList) {
                Row row = s5.createRow(r5++);
                row.createCell(0).setCellValue(r.getTitle());
                row.createCell(1).setCellValue(r.getPriority());
                row.createCell(2).setCellValue(r.getReason());
            }

            wb.write(baos);
            return baos.toByteArray();
        }
    }
}
