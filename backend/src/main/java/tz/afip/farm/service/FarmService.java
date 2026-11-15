package tz.afip.farm.service;

import org.locationtech.jts.geom.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tz.afip.common.exception.ApiException;
import tz.afip.farm.dto.*;
import tz.afip.farm.entity.*;
import tz.afip.farm.repository.*;
import java.math.BigDecimal;
import java.util.List;

@Service
public class FarmService {

    private final FarmRepository farms;
    private final FarmBoundaryRepository boundaries;
    private final GeometryFactory gf = new GeometryFactory(new PrecisionModel(), 4326);

    public FarmService(FarmRepository f, FarmBoundaryRepository b) { this.farms = f; this.boundaries = b; }

    public Farm create(FarmRequest req) {
        Farm f = new Farm();
        f.setFarmerId(req.getFarmerId());
        f.setName(req.getName());
        return farms.save(f);
    }

    @Transactional
    public FarmBoundary setBoundary(Long farmId, BoundaryRequest req) {
        if (req.getCoordinates() == null || req.getCoordinates().size() < 4)
            throw ApiException.badRequest("Polygon needs at least 4 coordinates");

        List<double[]> c = req.getCoordinates();
        Coordinate[] coords = new Coordinate[c.size()];
        for (int i = 0; i < c.size(); i++) coords[i] = new Coordinate(c.get(i)[0], c.get(i)[1]);
        Polygon poly = gf.createPolygon(coords);
        if (!poly.isValid()) throw ApiException.badRequest("Invalid polygon geometry");

        Farm farm = farms.findById(farmId)
            .orElseThrow(() -> ApiException.notFound("Farm not found: " + farmId));

        FarmBoundary b = new FarmBoundary();
        b.setFarmId(farmId);
        b.setGeom(poly);
        boundaries.save(b);

        farm.setCentroid(poly.getCentroid());
        double degArea = poly.getArea();
        double m2 = degArea * 111_320.0 * 111_320.0;
        farm.setAreaHa(BigDecimal.valueOf(m2 / 10_000.0));
        farms.save(farm);
        return b;
    }

    public List<Farm> all() { return farms.findAll(); }
}
