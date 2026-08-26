/** Landing page: pitch summary and entry points into the two experiences. */
import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <section>
      <div className="home-hero">
        <span className="hero-badge">SIH prototype · AI tourist safety</span>
        <h2>Predictive tourist safety, not reactive alerts</h2>
        <p>
          Most safety systems wait for an SOS before help is positioned.
          This prototype clusters incident and risk data with DBSCAN, then
          uses a p-median style optimizer to recommend where patrol units
          should actually be stationed &mdash; before an incident happens,
          not after.
        </p>
      </div>

      <div className="card-grid">
        <Link className="card" to="/tourist">
          <h3>Tourist app</h3>
          <p>
            Live risk map, one-tap SOS with location sharing, and a
            verifiable digital ID.
          </p>
        </Link>
        <Link className="card" to="/authority">
          <h3>Authority command centre</h3>
          <p>
            Live incident and SOS map, AI-recommended patrol positions, and
            real-time coverage tracking.
          </p>
        </Link>
      </div>
    </section>
  );
}
