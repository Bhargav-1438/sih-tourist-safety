/** Shared API-layer types used across the service modules. */

/** Standard FastAPI validation-error body shape (422 responses). */
export interface ValidationErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ValidationErrorResponse {
  detail: ValidationErrorDetail[] | string;
}

/** Shared state shape for polled data sources (Prompt 11). */
export interface Pollable<T> {
  /** Last successful payload - retained when a later poll fails. */
  data: T | null;
  /** True only until the first successful response arrives. */
  loading: boolean;
  /** Most recent poll error (null once a poll succeeds again). */
  error: string | null;
  /** True while erroring but older data is still being displayed. */
  stale: boolean;
  /** ISO timestamp of the last successful poll. */
  lastUpdated: string | null;
}