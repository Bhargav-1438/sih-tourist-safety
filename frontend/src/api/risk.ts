/** Risk-engine API module (Prompt 5 endpoints). */
import { apiGet } from "./client";
import type { RiskHeatmapResponse, RiskZonesResponse } from "../types/risk";

export interface RiskEngineParams {
  eps_km?: number;
  min_samples?: number;
}

/** GET /api/risk-zones */
export function getRiskZones(params?: RiskEngineParams): Promise<RiskZonesResponse> {
  return apiGet<RiskZonesResponse>("/api/risk-zones", params);
}

/** GET /api/risk-heatmap */
export function getRiskHeatmap(params?: RiskEngineParams): Promise<RiskHeatmapResponse> {
  return apiGet<RiskHeatmapResponse>("/api/risk-heatmap", params);
}
