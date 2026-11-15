package tz.afip.farm.dto;
import java.util.List;

public class BoundaryRequest {
    private List<double[]> coordinates;
    public List<double[]> getCoordinates() { return coordinates; }
    public void setCoordinates(List<double[]> c) { this.coordinates = c; }
}
