/** Emergency SOS flow: idle -> confirm -> sending -> active (or error). */
import { useState } from "react";
import { createSosEvent } from "../../api/sos";
import type { SOSEvent } from "../../types/sos";

type SosPhase = "idle" | "confirming" | "sending" | "active" | "error";

interface SosPanelProps {
  touristId: number;
  /** [latitude, longitude] that will be shared with authorities. */
  position: [number, number];
  /** Notifies the dashboard so the safety banner can switch to SOS ACTIVE. */
  onActivated: (event: SOSEvent) => void;
}

export default function SosPanel({
  touristId,
  position,
  onActivated,
}: SosPanelProps) {
  const [phase, setPhase] = useState<SosPhase>("idle");
  const [event, setEvent] = useState<SOSEvent | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function sendSos() {
    setPhase("sending");
    setError(null);
    try {
      const created = await createSosEvent({
        tourist_id: touristId,
        latitude: position[0],
        longitude: position[1],
      });
      setEvent(created);
      setPhase("active");
      onActivated(created);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? `${cause.message} Your SOS was NOT sent - press Send SOS again.`
          : "Your SOS was NOT sent - please retry.",
      );
      setPhase("error");
    }
  }

  if (phase === "active" && event) {
    return (
      <section className="tourist-card sos-active" aria-live="polite">
        <h2>SOS ACTIVE</h2>
        <p className="sos-note">Authorities have been notified (prototype).</p>
        <dl className="sos-details">
          <div>
            <dt>SOS ID</dt>
            <dd>#{event.id}</dd>
          </div>
          <div>
            <dt>Raised at</dt>
            <dd>{new Date(event.created_at).toLocaleString()}</dd>
          </div>
          <div>
            <dt>Location</dt>
            <dd>
              {event.latitude.toFixed(5)}, {event.longitude.toFixed(5)}
            </dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{event.status}</dd>
          </div>
        </dl>
      </section>
    );
  }

  if (phase === "confirming") {
    return (
      <section className="tourist-card sos-confirm" aria-live="polite">
        <h2>Send emergency SOS?</h2>
        <p>Your current location will be shared with authorities.</p>
        <p className="sos-coords">
          {position[0].toFixed(5)}, {position[1].toFixed(5)}
        </p>
        <div className="btn-row">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setPhase("idle")}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-danger"
            onClick={sendSos}
          >
            Send SOS
          </button>
        </div>
      </section>
    );
  }

  if (phase === "sending") {
    return (
      <section className="tourist-card sos-confirm" aria-live="polite">
        <h2>Send emergency SOS?</h2>
        <p className="sos-sending" role="status">
          Sending SOS…
        </p>
      </section>
    );
  }

  return (
    <section className="tourist-card sos-panel">
      <h2>Emergency SOS</h2>
      {phase === "error" && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      <button
        type="button"
        className="btn btn-sos"
        onClick={() => setPhase("confirming")}
      >
        SOS
      </button>
      <p className="muted sos-hint">
        Opens a confirmation step before anything is sent.
      </p>
    </section>
  );
}