package tz.afip.vegetation;

import org.springframework.stereotype.Service;
import java.io.BufferedReader;
import java.io.FileReader;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Service
public class NasaCsvParser {

    public static class Row {
        public String id;
        public LocalDate date;
        public BigDecimal ndvi;
        public String quality;
        public String modlandDescription;
    }

    public List<Row> parseCsv(String filePath) throws Exception {
        List<Row> rows = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String header = br.readLine();
            if (header == null) return rows;
            String[] cols = header.split(",");

            int idxId = findColumn(cols, "ID");
            int idxDate = findColumn(cols, "Date");
            int idxNdvi = findColumn(cols, "MOD13Q1_061__250m_16_days_NDVI");
            int idxQuality = findColumn(cols, "MOD13Q1_061__250m_16_days_VI_Quality");
            int idxModland = findColumn(cols, "MOD13Q1_061__250m_16_days_VI_Quality_MODLAND_Description");

            if (idxNdvi < 0 || idxDate < 0) {
                throw new IllegalArgumentException("CSV missing NDVI or Date column");
            }

            String line;
            while ((line = br.readLine()) != null) {
                String[] parts = line.split(",", -1);
                if (parts.length <= idxNdvi) continue;
                Row r = new Row();
                r.id = idxId >= 0 && idxId < parts.length ? parts[idxId] : null;
                r.date = LocalDate.parse(parts[idxDate]);
                r.ndvi = new BigDecimal(parts[idxNdvi]);
                r.quality = idxQuality >= 0 && idxQuality < parts.length ? parts[idxQuality] : null;
                r.modlandDescription = idxModland >= 0 && idxModland < parts.length ? parts[idxModland] : null;
                rows.add(r);
            }
        }
        return rows;
    }

    private int findColumn(String[] cols, String name) {
        for (int i = 0; i < cols.length; i++) {
            if (cols[i].trim().equals(name)) return i;
        }
        return -1;
    }
}
