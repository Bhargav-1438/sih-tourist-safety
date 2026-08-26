/** Risk-engine types - mirror backend/app/schemas/risk.py exactly. */

export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

export interface RiskZone {
  zone_id: number;
  center_latitude: number;
  center_longitude: number;
  radius_meters: number;
  point_count: number;
  incident_count: number;
  sos_count: number;
  dominant_incident_type: string;
  avg_severity: number;
  distinct_types: number;
  last_event_at: string;
  risk_score: number;
  risk_level: RiskLevel;
}

export interface RiskZonesResponse {
  generated_at: string;
  eps_km: number;
  min_samples: number;
  total_incidents: number;
  total_sos: number;
  noise_incidents: number;
  noise_sos: number;
  zone_count: number;
  zones: RiskZone[];
}

export interface HeatmapMarker {
  zone_id: number;
  /** [latitude, longitude] - Leaflet order. */
  center: [number, number];
  radius_meters: number;
  risk_score: number;
  risk_level: RiskLevel;
  point_count: number;
  incident_count: number;
  sos_count: number;
  dominant_incident_type: string;
  avg_severity: number;
  last_event_at: string;
}

export interface RiskHeatmapResponse {
  generated_at: string;
  eps_km: number;
  min_samples: number;
  total_incidents: number;
  total_sos: number;
  noise_incidents: number;
  noise_sos: number;
  marker_count: number;
  markers: HeatmapMarker[];
}