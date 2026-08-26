/** Digital-ID generation & verification API module. */
import { apiPost } from "./client";
import type {
  DigitalIdResponse,
  VerificationResponse,
  VerifyDigitalIdPayload,
} from "../types/tourist";

/** POST /api/digital-id/{tourist_id} */
export function createDigitalId(touristId: number): Promise<DigitalIdResponse> {
  return apiPost<DigitalIdResponse>(`/api/digital-id/${touristId}`);
}

/** POST /api/verify-id */
export function verifyDigitalId(payload: VerifyDigitalIdPayload): Promise<VerificationResponse> {
  return apiPost<VerificationResponse>("/api/verify-id", payload);
}
