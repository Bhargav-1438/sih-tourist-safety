/** Tourist / digital-ID / verification types.
 *  Mirror backend/app/schemas/tourist.py and schemas/digital_id.py exactly.
 */

export interface Tourist {
  id: number;
  name: string;
  phone: string;
  created_at: string;
}

export interface TouristCreatePayload {
  name: string;
  phone: string;
}

export interface DigitalIdResponse {
  tourist_id: number;
  token: string;
  expires_at: string;
  qr_code: string;
}

export interface VerifiedTourist {
  id: number;
  name: string;
}

export interface VerifyDigitalIdPayload {
  token: string;
}

export interface VerificationResponse {
  valid: boolean;
  tourist: VerifiedTourist | null;
}