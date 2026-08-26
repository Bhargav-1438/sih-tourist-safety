/** Shared visual styling for risk levels across all map surfaces. */
import type { RiskLevel } from "../../types/risk";

export const LEVEL_COLORS: Record<RiskLevel, string> = {
  CRITICAL: "#c53030",
  HIGH: "#dd6b20",
  MODERATE: "#d69e2e",
  LOW: "#38a169",
};

export function levelColor(level: RiskLevel): string {
  return LEVEL_COLORS[level];
}