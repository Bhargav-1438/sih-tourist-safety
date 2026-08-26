/**
 * Frontend-only REFERENCE / DEMO visualization data.
 *
 * These points and zones are NOT real data and are NOT connected to the
 * backend, risk engine, database, incidents, or patrol optimization. They
 * exist solely so the maps render meaningful context when the backend has no
 * data (or for orientation around the Vijayawada demo geography).
 *
 * Real API data ALWAYS takes precedence over anything in this file.
 */
import type { HeatmapMarker } from "../types/risk";

export interface TourismReference {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  kind: string;
}

/** Curated Vijayawada / Amaravati tourism reference points (demo only). */
export const TOURISM_REFERENCES: TourismReference[] = [
  {
    id: "kanaka-durga",
    name: "Kanaka Durga Temple",
    latitude: 16.5193,
    longitude: 80.6205,
    kind: "temple",
  },
  {
    id: "prakasam-barrage",
    name: "Prakasam Barrage",
    latitude: 16.5062,
    longitude: 80.648,
    kind: "landmark",
  },
  {
    id: "bhavani-island",
    name: "Bhavani Island",
    latitude: 16.4846,
    longitude: 80.554,
    kind: "island",
  },
  {
    id: "undavalli-caves",
    name: "Undavalli Caves",
    latitude: 16.4977,
    longitude: 80.5858,
    kind: "heritage",
  },
  {
    id: "gandhi-hill",
    name: "Gandhi Hill",
    latitude: 16.5135,
    longitude: 80.6217,
    kind: "viewpoint",
  },
  {
    id: "mangalagiri-temple",
    name: "Mangalagiri Temple",
    latitude: 16.4408,
    longitude: 80.557,
    kind: "temple",
  },
];

/**
 * Synthetic risk zones used ONLY as a visual fallback when the backend
 * returns no risk zones. zone_id >= 9000 so they can never collide with real
 * backend zone ids (which start at 1).
 */
export const DEMO_RISK_ZONES: HeatmapMarker[] = [
  {
    zone_id: 9001,
    center: [16.5193, 80.6205],
    radius_meters: 900,
    risk_score: 88,
    risk_level: "CRITICAL",
    point_count: 18,
    incident_count: 18,
    sos_count: 0,
    dominant_incident_type: "theft",
    avg_severity: 3.6,
    last_event_at: "2026-08-20T12:00:00",
  },
  {
    zone_id: 9002,
    center: [16.5062, 80.648],
    radius_meters: 700,
    risk_score: 55,
    risk_level: "HIGH",
    point_count: 12,
    incident_count: 12,
    sos_count: 0,
    dominant_incident_type: "harassment",
    avg_severity: 2.8,
    last_event_at: "2026-08-18T18:00:00",
  },
  {
    zone_id: 9003,
    center: [16.4846, 80.554],
    radius_meters: 800,
    risk_score: 40,
    risk_level: "MODERATE",
    point_count: 9,
    incident_count: 9,
    sos_count: 0,
    dominant_incident_type: "accident",
    avg_severity: 2.4,
    last_event_at: "2026-08-15T09:00:00",
  },
  {
    zone_id: 9004,
    center: [16.4977, 80.5858],
    radius_meters: 600,
    risk_score: 20,
    risk_level: "LOW",
    point_count: 6,
    incident_count: 6,
    sos_count: 0,
    dominant_incident_type: "unsafe_area",
    avg_severity: 1.8,
    last_event_at: "2026-08-12T10:30:00",
  },
];
