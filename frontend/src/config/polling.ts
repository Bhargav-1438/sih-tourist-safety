/** Centralized polling configuration (milliseconds), env-overridable. */

function readInterval(envKey: string, fallback: number): number {
  const raw = import.meta.env[envKey] as string | undefined;
  const parsed = raw ? Number.parseInt(raw, 10) : Number.NaN;
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export const POLL_INTERVALS = {
  /** Authority SOS feed - most urgent. */
  sos: readInterval("SOS_POLL_MS", 5_000),
  /** Risk zones + incidents - moderate. */
  risk: readInterval("RISK_POLL_MS", 15_000),
  /** Patrol plan + AI recommendations - least frequent. */
  patrol: readInterval("PATROL_POLL_MS", 30_000),
} as const;