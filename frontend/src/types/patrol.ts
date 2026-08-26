/** Patrol-optimization types - mirror backend/app/schemas/patrol.py exactly. */
import type { RiskLevel } from "./risk";

export interface PatrolUnit {
  unit_id: number;
  latitude: number;
  longitude: number;
  covers_zone_ids: number[];
  covered_zone_count: number;
  covered_weight: number;
  coverage_share_pct: number;
  avg_zone_distance_km: number;
  highest_risk_level: RiskLevel;
}

export interface UncoveredZone {
  zone_id: number;
  risk_score: number;
  risk_level: RiskLevel;
  center_latitude: number;
  center_longitude: number;
}

export interface PatrolPlanResponse {
  generated_at: string;
  algorithm: "greedy_pmedian_weighted_coverage";
  requested_units: number;
  placed_units: number;
  service_radius_km: number;
  total_zones: number;
  total_weight: number;
  covered_weight: number;
  coverage_pct: number;
  patrols: PatrolUnit[];
  uncovered_zones: UncoveredZone[];
}

export interface ServedZone {
  zone_id: number;
  risk_score: number;
  risk_level: RiskLevel;
  distance_km: number;
}

export interface PatrolRecommendation {
  unit_id: number;
  /** [latitude, longitude] - Leaflet order. */
  position: [number, number];
  service_radius_km: number;
  covers_zone_ids: number[];
  covered_zone_count: number;
  covered_weight: number;
  coverage_share_pct: number;
  avg_zone_distance_km: number;
  highest_risk_level: RiskLevel;
  served_zones: ServedZone[];
}

export interface PatrolRecommendationsResponse {
  generated_at: string;
  algorithm: "greedy_pmedian_weighted_coverage";
  requested_units: number;
  placed_units: number;
  service_radius_km: number;
  total_zones: number;
  total_weight: number;
  covered_weight: number;
  coverage_pct: number;
  recommendations: PatrolRecommendation[];
  uncovered_zones: UncoveredZone[];
}