/** Landing page: project overview, section navigation, map foundation check. */
import { Circle, Popup } from "react-leaflet";
import { Link } from "react-router-dom";
import MapView from "../components/common/MapView";

export default function HomePage() {
  return (
    <section>
      <h2>SIH Tourist Safety Prototype</h2>
      <p>
        Predictive Tourist Safety &amp; Resource Optimization using AI-driven
        risk clustering and geo-fencing. This prototype runs on a FastAPI +
        SQLite backend with a deterministic synthetic incident dataset.
      </p>

      <div className="card-grid">
        <Link className="card" to="/tourist">
          <h3>Tourist</h3>
          <p>Registration, digital ID, and SOS features (upcoming prompts).</p>
        </Link>
        <Link className="card" to="/authority">
          <h3>Authority</h3>
          <p>Risk heatmap and patrol recommendations (upcoming prompts).</p>
        </Link>
      </div>

      <h3>Map foundation</h3>
      <p>
        Shared <code>&lt;MapView /&gt;</code> component with a neutral
        foundation-check circle at the Vijayawada demo center.
      </p>
      <MapView className="map-view">
        <Circle
          center={[16.5062, 80.648]}
          radius={600}
          pathOptions={{ color: "#2b6cb0", fillOpacity: 0.15 }}
        >
          <Popup>Map foundation is rendering correctly.</Popup>
        </Circle>
      </MapView>
    </section>
  );
}
