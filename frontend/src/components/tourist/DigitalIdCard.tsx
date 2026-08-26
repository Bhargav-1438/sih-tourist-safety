/** Digital-ID card: loads the signed token + QR from the backend. */
import { useEffect, useState } from "react";
import { createDigitalId } from "../../api/digitalId";
import type { DigitalIdResponse } from "../../types/tourist";

interface DigitalIdCardProps {
  tourist: { id: number; name: string };
  onClose: () => void;
}

type LoadState =
  | { phase: "loading" }
  | { phase: "loaded"; data: DigitalIdResponse }
  | { phase: "error"; message: string };

export default function DigitalIdCard({ tourist, onClose }: DigitalIdCardProps) {
  const [state, setState] = useState<LoadState>({ phase: "loading" });

  function load() {
    setState({ phase: "loading" });
    createDigitalId(tourist.id)
      .then((data) => setState({ phase: "loaded", data }))
      .catch((cause: unknown) =>
        setState({
          phase: "error",
          message:
            cause instanceof Error
              ? cause.message
              : "Could not load your Digital ID.",
        }),
      );
  }

  useEffect(load, [tourist.id]);

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Digital ID"
      onClick={onClose}
    >
      <div
        className="digital-id-card"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="digital-id-header">
          <span>SIH TOURIST SAFETY</span>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close digital ID"
          >
            ×
          </button>
        </header>

        {state.phase === "loading" && (
          <p className="digital-id-body" role="status">
            Issuing digitally-signed ID…
          </p>
        )}

        {state.phase === "error" && (
          <div className="digital-id-body">
            <p role="alert" className="form-error">
              {state.message}
            </p>
            <button type="button" className="btn btn-secondary" onClick={load}>
              Retry
            </button>
          </div>
        )}

        {state.phase === "loaded" && (
          <div className="digital-id-body">
            <p className="digital-id-name">{tourist.name}</p>
            <p className="digital-id-meta">
              Tourist ID: <strong>#{tourist.id}</strong>
            </p>
            <img
              className="digital-id-qr"
              src={state.data.qr_code}
              alt={`QR code encoding the signed digital ID for tourist #${tourist.id}`}
            />
            <p className="digital-id-meta">
              Valid until:{" "}
              {new Date(state.data.expires_at).toLocaleString()}
            </p>
            <p className="digital-id-signature">
              Digitally signed &amp; issued by the SIH backend (HS256 JWT).
            </p>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}