/** Patrol-optimization API module (Prompt 6 endpoints). */
import { apiGet } from "./client";
import type {
  PatrolPlanResponse,
  PatrolRecommendationsResponse,
} from "../types/patrol";

export interface PatrolParams {
  units?: number;
  service_radius_km?: number;
  eps_km?: number;
  min_samples?: number;
}

/** GET /api/patrol-plan */
export function getPatrolPlan(params?: PatrolParams): Promise<PatrolPlanResponse> {
  return apiGet<PatrolPlanResponse>("/api/patrol-plan", params);
}

/** GET /api/patrol-recommendations */
export function getPatrolRecommendations(
  params?: PatrolParams,
): Promise<PatrolRecommendationsResponse> {
  return apiGet<PatrolRecommendationsResponse>("/api/patrol-recommendations", params);
}
