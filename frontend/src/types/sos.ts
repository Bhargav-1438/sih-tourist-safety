/** Incident & SOS types - mirror backend/app/schemas/incident.py exactly. */

export const INCIDENT_TYPES = [
  "theft",
  "harassment",
  "medical",
  "accident",
  "missing_person",
  "unsafe_area",
] as const;

export type IncidentType = (typeof INCIDENT_TYPES)[number];

export type SOSStatus = "active" | "resolved";

export interface Incident {
  id: number;
  latitude: number;
  longitude: number;
  incident_type: string;
  severity: number;
  occurred_at: string;
}

export interface SOSCreatePayload {
  tourist_id: number;
  latitude: number;
  longitude: number;
}

export interface SOSEvent {
  id: number;
  tourist_id: number;
  latitude: number;
  longitude: number;
  status: SOSStatus;
  created_at: string;
}

export interface SOSListResponse {
  sos_events: SOSEvent[];
}