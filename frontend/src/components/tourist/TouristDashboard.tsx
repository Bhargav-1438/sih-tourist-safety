/** Tourist dashboard: safety status, map, SOS, identity, digital ID. */
import { useCallback, useEffect, useState } from "react";
import { getRiskHeatmap } from "../../api/risk";
import type { HeatmapMarker } from "../../types/risk";
import type { Tourist } from "../../types/tourist";
import DigitalIdCard from "./DigitalIdCard";
import RiskMap from "./RiskMap";
import SosPanel from "./SosPanel";

/** Documented prototype fallback when geolocation is denied/unavailable. */
const DEMO_POSITION: [number, number] = [16.5062, 80.648];

interface TouristDashboardProps {
  tourist: Tourist;
  onRegisterDifferent: () => void;
}

type HeatmapState =
  | { phase: "loading" }
  | { phase: "loaded"; markers: HeatmapMarker[] }
  | { phase: "error"; message: string };

export default function TouristDashboard({
  tourist,
  onRegisterDifferent,
}: TouristDashboardProps) {
  const [position, setPosition] = useState<[number, number]>(DEMO_POSITION);
  const [positionIsDemo, setPositionIsDemo] = useState(true);
  const [heatmap, setHeatmap] = useState<HeatmapState>({ phase: "loading" });
  const [sosActive, setSosActive] = useState(false);
  const [showDigitalId, setShowDigitalId] = useState(false);

  const loadHeatmap = useCallback(() => {
    setHeatmap({ phase: "loading" });
    getRiskHeatmap()
      .then((response) =>
        setHeatmap({ phase: "loaded", markers: response.markers }),
      )
      .catch((cause: unknown) =>
        setHeatmap({
          phase: "error",
          message:
            cause instanceof Error ? cause.message : "Request failed.",
        }),
      );
  }, []);

  // Fetch the risk heatmap ONCE when the dashboard loads (no polling yet).
  useEffect(() => {
    loadHeatmap();
  }, [loadHeatmap]);

  // Request the browser location once. On denial/error keep the documented
  // Vijayawada fallback so the demo never blocks.
  useEffect(() => {
    if (!("geolocation" in navigator)) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setPosition([pos.coords.latitude, pos.coords.longitude]);
        setPositionIsDemo(false);
      },
      () => {
        /* Denied or unavailable - keep demo fallback. */
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 60_000 },
    );
  }, []);

  return (
    <div className="tourist-page">
      <div
        className={`status-banner ${sosActive ? "status-alert" : "status-safe"}`}
        role="status"
      >
        {sosActive
          ? "SOS ACTIVE - authorities notified"
          : "You are monitored. Tap SOS in an emergency."}
      </div>

      <SosPanel
        touristId={tourist.id}
        position={position}
        onActivated={() => setSosActive(true)}
      />

      <section className="tourist-card">
        <h2>Risk zones near you</h2>
        {positionIsDemo && (
          <p className="demo-note" role="note">
            Using the Vijayawada demo location (geolocation unavailable or
            denied).
          </p>
        )}
        <RiskMap
          markers={heatmap.phase === "loaded" ? heatmap.markers : []}
          userPosition={position}
          userPositionIsDemo={positionIsDemo}
          loading={heatmap.phase === "loading"}
          error={heatmap.phase === "error" ? heatmap.message : null}
          onRetry={loadHeatmap}
        />
      </section>

      <section className="tourist-card identity-card">
        <h2>Your profile</h2>
        <dl className="identity-details">
          <div>
            <dt>Name</dt>
            <dd>{tourist.name}</dd>
          </div>
          <div>
            <dt>Tourist ID</dt>
            <dd>#{tourist.id}</dd>
          </div>
          <div>
            <dt>Phone</dt>
            <dd>{tourist.phone}</dd>
          </div>
        </dl>

        <button
          type="button"
          className="btn btn-primary btn-block"
          onClick={() => setShowDigitalId(true)}
        >
          View Digital ID
        </button>
        <button
          type="button"
          className="link-button"
          onClick={onRegisterDifferent}
        >
          Not you? Register a different tourist
        </button>
      </section>

      {showDigitalId && (
        <DigitalIdCard
          tourist={{ id: tourist.id, name: tourist.name }}
          onClose={() => setShowDigitalId(false)}
        />
      )}
    </div>
  );
}