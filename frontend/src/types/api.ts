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