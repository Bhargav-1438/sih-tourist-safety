/** Risk-zone map: heatmap markers + current tourist position + legend. */
import { Circle, CircleMarker, Popup } from "react-leaflet";
import MapView from "../common/MapView";
import type { HeatmapMarker, RiskLevel } from "../../types/risk";
import { LEVEL_COLORS } from "../common/riskStyles";
import { TOURISM_REFERENCES, DEMO_RISK_ZONES } from "../../data/tourismReferences";

const USER_COLOR = "#2b6cb0";
const TOURISM_COLOR = "#7f9cf5";

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

  // Real API data always takes precedence. Reference layers only render when
  // the backend returned no risk zones.
  const showReferenceData = markers.length === 0;

  return (
    <div className="risk-map-wrap">
      {showReferenceData && (
        <div className="reference-badge" role="note">
          REFERENCE / DEMO DATA
        </div>
      )}
      <MapView center={userPosition} zoom={13}>
        {/* Real risk zones (backend data) */}
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

        {/* Reference / demo fallback risk zones - only when no real zones */}
        {showReferenceData &&
          DEMO_RISK_ZONES.map((marker) => (
            <Circle
              key={`demo-zone-${marker.zone_id}`}
              center={marker.center}
              radius={marker.radius_meters}
              pathOptions={{
                color: LEVEL_COLORS[marker.risk_level],
                fillColor: LEVEL_COLORS[marker.risk_level],
                fillOpacity: 0.18,
                weight: 1.5,
                dashArray: "6 5",
              }}
            >
              <Popup>
                <strong>REFERENCE zone - {marker.risk_level}</strong>
                <br />
                Score {marker.risk_score}/100 (demo data)
                <br />
                Dominant: {marker.dominant_incident_type}
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

        {/* Reference tourism points - only with reference data */}
        {showReferenceData &&
          TOURISM_REFERENCES.map((ref) => (
            <CircleMarker
              key={`ref-${ref.id}`}
              center={[ref.latitude, ref.longitude]}
              radius={6}
              pathOptions={{
                color: "#ffffff",
                weight: 1.5,
                fillColor: TOURISM_COLOR,
                fillOpacity: 1,
              }}
            >
              <Popup>
                <strong>{ref.name}</strong>
                <br />
                {ref.kind}
                <br />
                Reference point (demo)
              </Popup>
            </CircleMarker>
          ))}
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
        {showReferenceData && (
          <span className="legend-item">
            <span
              className="legend-swatch"
              style={{ backgroundColor: TOURISM_COLOR }}
              aria-hidden="true"
            />
            Reference point
          </span>
        )}
      </div>
    </div>
  );
}