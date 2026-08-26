/** Authority command centre: five live backend datasets on one screen. */
import { useCallback, useEffect, useState } from "react";
import { getRiskHeatmap } from "../api/risk";
import { getIncidents } from "../api/incidents";
import { getSosEvents } from "../api/sos";
import { getPatrolPlan, getPatrolRecommendations } from "../api/patrol";
import type { RiskHeatmapResponse } from "../types/risk";
import type { Incident } from "../types/sos";
import type { SOSListResponse } from "../types/sos";
import type {
  PatrolPlanResponse,
  PatrolRecommendationsResponse,
} from "../types/patrol";
import SafetyMap from "../components/authority/SafetyMap";
import StatCards from "../components/authority/StatCards";
import PatrolPanel from "../components/authority/PatrolPanel";

type Loadable<T> =
  | { state: "loading" }
  | { state: "ready"; data: T }
  | { state: "error"; message: string };

function errorMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : "Request failed.";
}

export default function AuthorityPage() {
  const [heatmap, setHeatmap] = useState<Loadable<RiskHeatmapResponse>>({
    state: "loading",
  });
  const [incidents, setIncidents] = useState<Loadable<Incident[]>>({
    state: "loading",
  });
  const [sos, setSos] = useState<Loadable<SOSListResponse>>({ state: "loading" });
  const [plan, setPlan] = useState<Loadable<PatrolPlanResponse>>({
    state: "loading",
  });
  const [recs, setRecs] = useState<Loadable<PatrolRecommendationsResponse>>({
    state: "loading",
  });

  const loadHeatmap = useCallback(() => {
    setHeatmap({ state: "loading" });
    getRiskHeatmap()
      .then((data) => setHeatmap({ state: "ready", data }))
      .catch((cause) => setHeatmap({ state: "error", message: errorMessage(cause) }));
  }, []);
  const loadIncidents = useCallback(() => {
    setIncidents({ state: "loading" });
    getIncidents()
      .then((data) => setIncidents({ state: "ready", data }))
      .catch((cause) => setIncidents({ state: "error", message: errorMessage(cause) }));
  }, []);
  const loadSos = useCallback(() => {
    setSos({ state: "loading" });
    getSosEvents()
      .then((data) => setSos({ state: "ready", data }))
      .catch((cause) => setSos({ state: "error", message: errorMessage(cause) }));
  }, []);
  const loadPlan = useCallback(() => {
    setPlan({ state: "loading" });
    getPatrolPlan()
      .then((data) => setPlan({ state: "ready", data }))
      .catch((cause) => setPlan({ state: "error", message: errorMessage(cause) }));
  }, []);
  const loadRecs = useCallback(() => {
    setRecs({ state: "loading" });
    getPatrolRecommendations()
      .then((data) => setRecs({ state: "ready", data }))
      .catch((cause) => setRecs({ state: "error", message: errorMessage(cause) }));
  }, []);

  // Single snapshot fetch on mount; Prompt 11 adds refresh/polling.
  useEffect(() => {
    loadHeatmap();
    loadIncidents();
    loadSos();
    loadPlan();
    loadRecs();
  }, [loadHeatmap, loadIncidents, loadSos, loadPlan, loadRecs]);

  const markers = heatmap.state === "ready" ? heatmap.data.markers : [];
  const incidentList = incidents.state === "ready" ? incidents.data : [];
  const sosEvents = sos.state === "ready" ? sos.data.sos_events : [];
  const activeSosCount = sosEvents.filter((s) => s.status === "active").length;
  const criticalHigh = markers.filter(
    (m) => m.risk_level === "CRITICAL" || m.risk_level === "HIGH",
  ).length;

  return (
    <div className="authority-page">
      <h2>Authority command centre</h2>

      {(heatmap.state === "error" ||
        incidents.state === "error" ||
        sos.state === "error" ||
        plan.state === "error" ||
        recs.state === "error") && (
        <div className="authority-errors">
          {heatmap.state === "error" && (
            <span>
              Heatmap failed ({heatmap.message}){" "}
              <button type="button" onClick={loadHeatmap}>Retry</button>
            </span>
          )}
          {incidents.state === "error" && (
            <span>
              Incidents failed ({incidents.message}){" "}
              <button type="button" onClick={loadIncidents}>Retry</button>
            </span>
          )}
          {sos.state === "error" && (
            <span>
              SOS failed ({sos.message}){" "}
              <button type="button" onClick={loadSos}>Retry</button>
            </span>
          )}
          {plan.state === "error" && (
            <span>
              Patrol plan failed ({plan.message}){" "}
              <button type="button" onClick={loadPlan}>Retry</button>
            </span>
          )}
          {recs.state === "error" && (
            <span>
              Recommendations failed ({recs.message}){" "}
              <button type="button" onClick={loadRecs}>Retry</button>
            </span>
          )}
        </div>
      )}

      <StatCards
        totalIncidents={incidents.state === "ready" ? incidents.data.length : null}
        totalSos={sos.state === "ready" ? sos.data.sos_events.length : null}
        activeSos={sos.state === "ready" ? activeSosCount : null}
        riskZoneCount={heatmap.state === "ready" ? heatmap.data.marker_count : null}
        criticalHighZones={heatmap.state === "ready" ? criticalHigh : null}
        recommendedUnits={
          recs.state === "ready" ? recs.data.placed_units : null
        }
        coveragePct={recs.state === "ready" ? recs.data.coverage_pct : null}
      />

      <div className="authority-grid">
        <section className="tourist-card authority-map-card">
          <h2>Live safety map</h2>
          <SafetyMap
            markers={markers}
            incidents={incidentList}
            sosEvents={sosEvents}
            plan={plan.state === "ready" ? plan.data : null}
            recommendations={recs.state === "ready" ? recs.data.recommendations : []}
          />
        </section>

        <aside className="patrol-panel-wrap">
          <PatrolPanel
            recommendations={recs.state === "ready" ? recs.data : null}
            plan={plan.state === "ready" ? plan.data : null}
          />
        </aside>
      </div>
    </div>
  );
}