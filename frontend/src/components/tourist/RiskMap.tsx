/** Risk-zone map: heatmap markers + current tourist position + legend. */
import { Circle, Popup } from "react-leaflet";
import MapView from "../common/MapView";
import type { HeatmapMarker, RiskLevel } from "../../types/risk";

const LEVEL_COLORS: Record<RiskLevel, string> = {
  CRITICAL: "#c53030",
  HIGH: "#dd6b20",
  MODERATE: "#d69e2e",
  LOW: "#38a169",
};

const USER_COLOR = "#2b6cb0";

interface RiskMapProps {
  markers: HeatmapMarker[];
  /** [latitude, longitude] of the tourist current or demo-fallback position. */
  userPosition: [number, number];
  /** True when the Vijayawada fallback is used instead of real geolocation. */
  userPositionIsDemo: boolean;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export default function RiskMap({
  markers,
  userPosition,
  userPositionIsDemo,
  loading,
  error,
  onRetry,
}: RiskMapProps) {
  if (loading) {
    return (
      <div className="map-status" role="status">
        Loading risk zones...
      </div>
    );
  }

  if (error) {
    return (
      <div className="map-status map-status-error" role="alert">
        <p>Could not load risk zones: {error}</p>
        <button type="button" className="btn btn-secondary" onClick={onRetry}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <MapView center={userPosition} zoom={13}>
        {markers.map((marker) => (
          <Circle
            key={marker.zone_id}
            center={marker.center}
            radius={marker.radius_meters}
            pathOptions={{
              color: LEVEL_COLORS[marker.risk_level],
              fillColor: LEVEL_COLORS[marker.risk_level],
              fillOpacity: 0.18,
              weight: 1.5,
            }}
          >
            <Popup>
              <strong>
                {marker.risk_level} zone #{marker.zone_id}
              </strong>
              <br />
              Risk score: {marker.risk_score}/100
              <br />
              Incidents: {marker.incident_count} | SOS: {marker.sos_count}
              <br />
              Dominant type: {marker.dominant_incident_type}
              <br />
              Avg severity: {marker.avg_severity}
            </Popup>
          </Circle>
        ))}

        {/* Current tourist position (blue ring avoids shipping marker PNGs). */}
        <Circle
          center={userPosition}
          radius={60}
          pathOptions={{
            color: USER_COLOR,
            fillColor: USER_COLOR,
            fillOpacity: 0.35,
            weight: 2,
          }}
        >
          <Popup>
            {userPositionIsDemo
              ? "Demo location (Vijayawada fallback)"
              : "Your current location"}
          </Popup>
        </Circle>
      </MapView>

      <div className="map-legend">
        {(Object.keys(LEVEL_COLORS) as RiskLevel[]).map((level) => (
          <span key={level} className="legend-item">
            <span
              className="legend-swatch"
              style={{ backgroundColor: LEVEL_COLORS[level] }}
              aria-hidden="true"
            />
            {level}
          </span>
        ))}
        <span className="legend-item">
          <span
            className="legend-swatch legend-swatch-user"
            style={{ backgroundColor: USER_COLOR }}
            aria-hidden="true"
          />
          {userPositionIsDemo ? "Demo location" : "Current Location"}
        </span>
      </div>
    </div>
  );
}