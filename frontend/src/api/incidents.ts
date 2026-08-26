/** Incident API module. */
import { apiGet } from "./client";
import type { Incident } from "../types/sos";

/** GET /api/incidents - returns the full synthetic demo dataset. */
export function getIncidents(): Promise<Incident[]> {
  return apiGet<Incident[]>("/api/incidents");
}
