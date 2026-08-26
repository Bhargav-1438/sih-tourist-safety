/** Command-centre safety map: five data layers over the shared MapView. */
import { Circle, CircleMarker, Polyline, Popup } from "react-leaflet";
import MapView from "../common/MapView";
import { LEVEL_COLORS } from "../common/riskStyles";
import type { HeatmapMarker } from "../../types/risk";
import type { Incident, SOSEvent } from "../../types/sos";
import type {
  PatrolPlanResponse,
  PatrolRecommendation,
} from "../../types/patrol";
import { TOURISM_REFERENCES, DEMO_RISK_ZONES } from "../../data/tourismReferences";

const INCIDENT_COLOR = "#4a5568";
const SOS_COLOR = "#e53e3e";
const CURRENT_COLOR = "#2b6cb0";
const RECOMMENDED_COLOR = "#38a169";
const TOURISM_COLOR = "#7f9cf5";

interface SafetyMapProps {
  markers: HeatmapMarker[];
  incidents: Incident[];
  sosEvents: SOSEvent[];
  plan: PatrolPlanResponse | null;
  recommendations: PatrolRecommendation[];
}

export default function SafetyMap({
  markers,
  incidents,
  sosEvents,
  plan,
  recommendations,
}: SafetyMapProps) {
  // Real API data always takes precedence. Fallback zones render ONLY when
  // the backend returned no risk zones.
  const showReferenceZones = markers.length === 0;

  // Zone-center lookup so recommendation links can be drawn on-map.
  const zoneCenters = new Map(
    markers.map((m) => [m.zone_id, m.center] as const),
  );

  return (
    <div className="safety-map-wrap">
      {showReferenceZones && (
        <div className="reference-badge" role="note">
          REFERENCE / DEMO DATA
        </div>
      )}
      <MapView center={[16.5062, 80.648]} zoom={12}>
        {/* Layer 1 - risk zones (backend radii, level colours) */}
        {markers.map((marker) => (
          <Circle
            key={`zone-${marker.zone_id}`}
            center={marker.center}
            radius={marker.radius_meters}
            pathOptions={{
              color: LEVEL_COLORS[marker.risk_level],
              fillColor: LEVEL_COLORS[marker.risk_level],
              fillOpacity: 0.12,
              weight: 1.5,
            }}
          >
            <Popup>
              <strong>
                {marker.risk_level} zone #{marker.zone_id}
              </strong>
              <br />
              Score {marker.risk_score}/100
              <br />
              Incidents: {marker.incident_count} | SOS: {marker.sos_count}
              <br />
              Dominant: {marker.dominant_incident_type} | avg sev{" "}
              {marker.avg_severity}
            </Popup>
          </Circle>
        ))}

        {/* Reference / demo fallback risk zones - only when no real zones */}
        {showReferenceZones &&
          DEMO_RISK_ZONES.map((marker) => (
            <Circle
              key={`demo-zone-${marker.zone_id}`}
              center={marker.center}
              radius={marker.radius_meters}
              pathOptions={{
                color: LEVEL_COLORS[marker.risk_level],
                fillColor: LEVEL_COLORS[marker.risk_level],
                fillOpacity: 0.12,
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

        {/* Reference tourism points - distinct visual layer */}
        {TOURISM_REFERENCES.map((ref) => (
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

        {/* Layer 2 - historical incidents */}
        {incidents.map((incident) => (
          <CircleMarker
            key={`inc-${incident.id}`}
            center={[incident.latitude, incident.longitude]}
            radius={5}
            pathOptions={{
              color: "#ffffff",
              weight: 1,
              fillColor: INCIDENT_COLOR,
              fillOpacity: 1,
            }}
          >
            <Popup>
              <strong>{incident.incident_type}</strong> (severity{" "}
              {incident.severity}/5)
              <br />
              {new Date(incident.occurred_at).toLocaleString()}
              <br />
              [{incident.latitude.toFixed(5)}, {incident.longitude.toFixed(5)}]
            </Popup>
          </CircleMarker>
        ))}

        {/* Layer 3 - SOS events (urgent treatment) */}
        {sosEvents.map((sos) => (
          <CircleMarker
            key={`sos-${sos.id}`}
            center={[sos.latitude, sos.longitude]}
            radius={9}
            pathOptions={{
              color: "#ffffff",
              weight: 2,
              fillColor: SOS_COLOR,
              fillOpacity: 1,
            }}
          >
            <Popup>
              <strong>SOS #{sos.id}</strong> - {sos.status.toUpperCase()}
              <br />
              Tourist #{sos.tourist_id}
              <br />
              {new Date(sos.created_at).toLocaleString()}
              <br />
              [{sos.latitude.toFixed(5)}, {sos.longitude.toFixed(5)}]
            </Popup>
          </CircleMarker>
        ))}

        {/* Layer 4 - current patrol posts (from /api/patrol-plan) */}
        {plan?.patrols.map((unit) => (
          <CircleMarker
            key={`cur-${unit.unit_id}`}
            center={[unit.latitude, unit.longitude]}
            radius={8}
            pathOptions={{
              color: CURRENT_COLOR,
              fillColor: CURRENT_COLOR,
              fillOpacity: 0.15,
              weight: 2.5,
              dashArray: "5 4",
            }}
          >
            <Popup>
              <strong>Current post #{unit.unit_id}</strong>
              <br />
              Serves zones: {unit.covers_zone_ids.join(", ") || "-"}
              <br />
              <em>Source: GET /api/patrol-plan</em>
            </Popup>
          </CircleMarker>
        ))}

        {/* Layer 5 - AI-recommended units + reasoning links */}
        {recommendations.flatMap((rec) => {
          const lines = rec.covers_zone_ids
            .map((id) => zoneCenters.get(id))
            .filter((c): c is [number, number] => Boolean(c))
            .map((center) => (
              <Polyline
                key={`link-${rec.unit_id}-${center[0]}-${center[1]}`}
                positions={[rec.position, center]}
                pathOptions={{
                  color: RECOMMENDED_COLOR,
                  weight: 1.5,
                  opacity: 0.7,
                }}
              />
            ));
          const marker = (
            <CircleMarker
              key={`rec-${rec.unit_id}`}
              center={rec.position}
              radius={8}
              pathOptions={{
                color: "#ffffff",
                weight: 2,
                fillColor: RECOMMENDED_COLOR,
                fillOpacity: 1,
              }}
            >
              <Popup>
                <strong>AI unit #{rec.unit_id}</strong>
                <br />
                Covers zones: {rec.covers_zone_ids.join(", ")}
                <br />
                Coverage share: {rec.coverage_share_pct}%
              </Popup>
            </CircleMarker>
          );
          return [...lines, marker];
        })}
      </MapView>

      <div className="map-legend-card">
        <strong>Legend</strong>
        <ul>
          {(Object.keys(LEVEL_COLORS) as (keyof typeof LEVEL_COLORS)[]).map(
            (level) => (
              <li key={level}>
                <span
                  className="legend-dot"
                  style={{ background: LEVEL_COLORS[level], opacity: 0.55 }}
                />
                {level} zone
              </li>
            ),
          )}
          <li>
            <span className="legend-dot" style={{ background: INCIDENT_COLOR }} />
            Incident
          </li>
          <li>
            <span className="legend-dot" style={{ background: SOS_COLOR }} />
            SOS
          </li>
          <li>
            <span className="legend-ring" style={{ borderColor: CURRENT_COLOR }} />
            Current post
          </li>
          <li>
            <span className="legend-dot" style={{ background: RECOMMENDED_COLOR }} />
            AI recommended
          </li>
          <li>
            <span className="legend-dot" style={{ background: TOURISM_COLOR }} />
            Reference point
          </li>
        </ul>
      </div>
    </div>
  );
}