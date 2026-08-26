/** Tourist application entry: registration -> persisted dashboard + SOS. */
import { useState } from "react";
import RegistrationForm from "../components/tourist/RegistrationForm";
import TouristDashboard from "../components/tourist/TouristDashboard";
import type { Tourist } from "../types/tourist";
import type { SOSEvent } from "../types/sos";

// Minimum prototype identity/state persisted so a refresh keeps the demo.
const TOURIST_KEY = "sih_tourist";
const ACTIVE_SOS_KEY = "sih_sos_active";

function readJson<T>(key: string, isValid: (value: unknown) => value is T): T | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    return isValid(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function isTourist(value: unknown): value is Tourist {
  const v = value as Partial<Tourist>;
  return (
    typeof v.id === "number" &&
    typeof v.name === "string" &&
    typeof v.phone === "string" &&
    typeof v.created_at === "string"
  );
}

function isSosEvent(value: unknown): value is SOSEvent {
  const v = value as Partial<SOSEvent>;
  return (
    typeof v.id === "number" &&
    typeof v.tourist_id === "number" &&
    typeof v.latitude === "number" &&
    typeof v.longitude === "number" &&
    v.status === "active" &&
    typeof v.created_at === "string"
  );
}

export default function TouristPage() {
  const [tourist, setTourist] = useState<Tourist | null>(() =>
    readJson(TOURIST_KEY, isTourist),
  );
  // Only *active* events are restored; the backend keeps the full history.
  const [activeSos, setActiveSos] = useState<SOSEvent | null>(() =>
    tourist ? readJson(ACTIVE_SOS_KEY, isSosEvent) : null,
  );

  function handleRegistered(created: Tourist) {
    localStorage.setItem(TOURIST_KEY, JSON.stringify(created));
    setTourist(created);
    window.scrollTo({ top: 0 });
  }

  function handleSosActivated(event: SOSEvent) {
    localStorage.setItem(ACTIVE_SOS_KEY, JSON.stringify(event));
    setActiveSos(event);
  }

  function handleRegisterDifferent() {
    localStorage.removeItem(TOURIST_KEY);
    localStorage.removeItem(ACTIVE_SOS_KEY);
    setTourist(null);
    setActiveSos(null);
    window.scrollTo({ top: 0 });
  }

  return (
    <div className="tourist-page">
      {tourist ? (
        <TouristDashboard
          tourist={tourist}
          activeSos={activeSos}
          onSosActivated={handleSosActivated}
          onRegisterDifferent={handleRegisterDifferent}
        />
      ) : (
        <RegistrationForm onRegistered={handleRegistered} />
      )}
    </div>
  );
}
