/** Patrol reasoning panel: AI recommendations + current posts summary. */
import type {
  PatrolPlanResponse,
  PatrolRecommendationsResponse,
} from "../../types/patrol";

interface PatrolPanelProps {
  recommendations: PatrolRecommendationsResponse | null;
  plan: PatrolPlanResponse | null;
}

export default function PatrolPanel({
  recommendations,
  plan,
}: PatrolPanelProps) {
  return (
    <>
      <section className="tourist-card patrol-section">
        <h2>AI patrol recommendations</h2>
        {!recommendations && <p className="muted">Loading recommendations…</p>}

        {recommendations && recommendations.recommendations.length === 0 && (
          <p className="muted">
            No risk zones available yet - nothing to recommend.
          </p>
        )}

        {recommendations?.recommendations.map((rec) => (
          <article key={rec.unit_id} className="patrol-item">
            <header className="patrol-item-head">
              <strong>Unit #{rec.unit_id}</strong>
              <span
                className={`level-chip level-${rec.highest_risk_level.toLowerCase()}`}
              >
                {rec.highest_risk_level}
              </span>
            </header>
            <p className="patrol-position">
              Position: [{rec.position[0].toFixed(5)},{" "}
              {rec.position[1].toFixed(5)}]
            </p>

            <p className="coverage-caption">
              Covers {rec.covered_zone_count} zone(s): #{rec.covers_zone_ids.join(", #")}
            </p>
            <div
              className="coverage-bar"
              role="img"
              aria-label={`Coverage share ${rec.coverage_share_pct}%`}
            >
              <div
                className="coverage-fill"
                style={{ width: `${Math.min(100, rec.coverage_share_pct)}%` }}
              />
            </div>
            <p className="coverage-numbers">
              weight {rec.covered_weight} · {rec.coverage_share_pct}% of total
            </p>

            {rec.served_zones.length > 0 && (
              <ul className="served-zones">
                {rec.served_zones.map((zone) => (
                  <li key={zone.zone_id}>
                    Zone #{zone.zone_id} - {zone.risk_level} (score{" "}
                    {zone.risk_score}) - {zone.distance_km.toFixed(3)} km
                  </li>
                ))}
              </ul>
            )}
          </article>
        ))}

        {recommendations && recommendations.uncovered_zones.length > 0 && (
          <p className="uncovered-note">
            Uncovered zones:{" "}
            {recommendations.uncovered_zones
              .map((z) => `#${z.zone_id} (${z.risk_level})`)
              .join(", ")}
          </p>
        )}
      </section>

      <section className="tourist-card patrol-section">
        <h2>Current patrol posts</h2>
        {!plan && <p className="muted">Loading current posts…</p>}
        {plan && plan.patrols.length === 0 && (
          <p className="muted">No posts computed yet.</p>
        )}
        {plan?.patrols.map((unit) => (
          <p key={unit.unit_id} className="current-post-line">
            Post #{unit.unit_id} @ [{unit.latitude.toFixed(4)},{" "}
            {unit.longitude.toFixed(4)}] - zones #{unit.covers_zone_ids.join(", #")}
          </p>
        ))}
        <p className="source-note">
          Source: GET /api/patrol-plan (no live GPS feed in the prototype).
        </p>
      </section>
    </>
  );
}