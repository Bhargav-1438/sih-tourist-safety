/** Tourist registration API module. */
import { apiPost } from "./client";
import type {
  Tourist,
  TouristCreatePayload,
} from "../types/tourist";

/** POST /api/register */
export function registerTourist(payload: TouristCreatePayload): Promise<Tourist> {
  return apiPost<Tourist>("/api/register", payload);
}
