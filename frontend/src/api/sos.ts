/** SOS API module. */
import { apiGet, apiPost } from "./client";
import type {
  SOSCreatePayload,
  SOSListResponse,
} from "../types/sos";

/** POST /api/sos */
export function createSosEvent(payload: SOSCreatePayload): Promise<SOSListResponse["sos_events"][number]> {
  return apiPost("/api/sos", payload);
}

/** GET /api/sos */
export function getSosEvents(): Promise<SOSListResponse> {
  return apiGet<SOSListResponse>("/api/sos");
}
