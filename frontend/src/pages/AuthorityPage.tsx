/** Authority command centre: five live backend datasets on one screen. */
import { getRiskHeatmap } from "../api/risk";
import { getIncidents } from "../api/incidents";
import { getSosEvents } from "../api/sos";
import { getPatrolPlan, getPatrolRecommendations } from "../api/patrol";
import type { RiskHeatmapResponse } from "../types/risk";
import type { Incident, SOSListResponse } from "../types/sos";
import type {
  PatrolPlanResponse,
  PatrolRecommendationsResponse,
} from "../types/patrol";
import type { Pollable } from "../types/api";
import { usePolledSource } from "../hooks/usePolling";
import { POLL_INTERVALS } from "../config/polling";
import SafetyMap from "../components/authority/SafetyMap";
import StatCards from "../components/authority/StatCards";
import PatrolPanel from "../components/authority/PatrolPanel";

export default function AuthorityPage() {
  const heatmap = usePolledSource<RiskHeatmapResponse>(
    getRiskHeatmap,
    POLL_INTERVALS.risk,
  );
  const incidents = usePolledSource<Incident[]>(
    getIncidents,
    POLL_INTERVALS.risk,
  );
  const sos = usePolledSource<SOSListResponse>(
    getSosEvents,
    POLL_INTERVALS.sos,
  );
  const plan = usePolledSource<PatrolPlanResponse>(
    getPatrolPlan,
    POLL_INTERVALS.patrol,
  );
  const recommendations = usePolledSource<PatrolRecommendationsResponse>(
    getPatrolRecommendations,
    POLL_INTERVALS.patrol,
  );

  const sources: Record<string, Pollable<unknown>> = {
    heatmap: heatmap,
    incidents: incidents,
    sos: sos,
    plan: plan,
    recommendations: recommendations,
  };

  const staleSources = Object.entries(sources)
    .filter(([, s]) => s.stale)
    .map(([name]) => name);

  const blocked = Object.entries(sources).filter(
    ([, s]) => s.error !== null && s.data === null,
  );

  const markers = heatmap.data?.markers ?? [];
  const incidentList = incidents.data ?? [];
  const sosEvents = sos.data?.sos_events ?? [];
  const activeSosCount = sosEvents.filter((s) => s.status === "active").length;
  const criticalHigh = markers.filter(
    (m) => m.risk_level === "CRITICAL" || m.risk_level === "HIGH",
  ).length;

  return (
    <div className="authority-page">
      <h2>Authority command centre</h2>
      <p className="poll-note">
        Auto-refresh: SOS {POLL_INTERVALS.sos / 1000}s · risk {POLL_INTERVALS.risk / 1000}s ·
        patrol {POLL_INTERVALS.patrol / 1000}s
      </p>

      {staleSources.length > 0 && (
        <div className="stale-chip" role="status">
          Some data may be outdated ({staleSources.join(", ")}) - retrying
          automatically.
        </div>
      )}

      {blocked.map(([name, source]) => (
        <div key={name} className="authority-errors">
          <span>
            {name} failed ({source.error}){" "}
            <button
              type="button"
              onClick={() => {
                if (name === "heatmap") void heatmap.reload();
                if (name === "incidents") void incidents.reload();
                if (name === "sos") void sos.reload();
                if (name === "plan") void plan.reload();
                if (name === "recommendations") void recommendations.reload();
              }}
            >
              Retry
            </button>
          </span>
        </div>
      ))}

      <StatCards
        totalIncidents={incidentList.length || null}
        totalSos={sosEvents.length || null}
        activeSos={activeSosCount || null}
        riskZoneCount={markers.length || null}
        criticalHighZones={criticalHigh || null}
        recommendedUnits={recommendations.data?.placed_units ?? null}
        coveragePct={recommendations.data?.coverage_pct ?? null}
      />

      <div className="authority-grid">
        <section className="tourist-card authority-map-card">
          <h2>Live safety map</h2>
          <SafetyMap
            markers={markers}
            incidents={incidentList}
            sosEvents={sosEvents}
            plan={plan.data}
            recommendations={recommendations.data?.recommendations ?? []}
          />
        </section>

        <aside className="patrol-panel-wrap">
          <PatrolPanel
            recommendations={recommendations.data}
            plan={plan.data}
          />
        </aside>
      </div>
    </div>
  );
}