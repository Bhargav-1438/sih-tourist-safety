/** Tourist dashboard: safety status, map, SOS, identity, digital ID. */
import { useEffect, useState } from "react";
import { usePolledSource } from "../../hooks/usePolling";
import { POLL_INTERVALS } from "../../config/polling";
import { getRiskHeatmap } from "../../api/risk";
import type { Tourist } from "../../types/tourist";
import type { SOSEvent } from "../../types/sos";
import DigitalIdCard from "./DigitalIdCard";
import RiskMap from "./RiskMap";
import SosPanel from "./SosPanel";

/** Documented prototype fallback when geolocation is denied/unavailable. */
const DEMO_POSITION: [number, number] = [16.5062, 80.648];

interface TouristDashboardProps {
  tourist: Tourist;
  /** Restored/persisted active SOS event (null when none). */
  activeSos: SOSEvent | null;
  /** Called after a fresh SOS is accepted by the backend. */
  onSosActivated: (event: SOSEvent) => void;
  onRegisterDifferent: () => void;
}

export default function TouristDashboard({
  tourist,
  activeSos,
  onSosActivated,
  onRegisterDifferent,
}: TouristDashboardProps) {
  const [position, setPosition] = useState<[number, number]>(DEMO_POSITION);
  const [positionIsDemo, setPositionIsDemo] = useState(true);
  const [showDigitalId, setShowDigitalId] = useState(false);

  // Risk zones refresh periodically so newly generated zones appear.
  const heatmap = usePolledSource(getRiskHeatmap, POLL_INTERVALS.risk);

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

  const sosActive = activeSos !== null;

  return (
    <div className="tourist-page">
      <div
        className={`status-banner ${sosActive ? "status-alert" : "status-safe"}`}
        role="status"
      >
        {sosActive
          ? `SOS ACTIVE - authorities notified (#${activeSos.id})`
          : "You are monitored. Tap SOS in an emergency."}
      </div>

      <SosPanel
        touristId={tourist.id}
        position={position}
        initialEvent={activeSos}
        onActivated={onSosActivated}
      />

      <section className="tourist-card">
        <h2>Risk zones near you</h2>
        {heatmap.stale && (
          <p className="stale-chip" role="status">
            Risk data may be outdated - retrying automatically.
          </p>
        )}
        {positionIsDemo && (
          <p className="demo-note" role="note">
            Using the Vijayawada demo location (geolocation unavailable or
            denied).
          </p>
        )}
        <RiskMap
          markers={heatmap.data?.markers ?? []}
          userPosition={position}
          userPositionIsDemo={positionIsDemo}
          loading={heatmap.loading}
          error={heatmap.data === null ? heatmap.error : null}
          onRetry={heatmap.reload}
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