/** Tourist application entry: registration -> persisted dashboard. */
import { useState } from "react";
import RegistrationForm from "../components/tourist/RegistrationForm";
import TouristDashboard from "../components/tourist/TouristDashboard";
import type { Tourist } from "../types/tourist";

// Minimum prototype identity persisted so a refresh keeps the demo alive.
const STORAGE_KEY = "sih_tourist";

function readStoredTourist(): Tourist | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<Tourist>;
    if (
      typeof parsed.id === "number" &&
      typeof parsed.name === "string" &&
      typeof parsed.phone === "string" &&
      typeof parsed.created_at === "string"
    ) {
      return parsed as Tourist;
    }
    return null;
  } catch {
    return null;
  }
}

export default function TouristPage() {
  const [tourist, setTourist] = useState<Tourist | null>(
    () => readStoredTourist(),
  );

  function handleRegistered(created: Tourist) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(created));
    setTourist(created);
    window.scrollTo({ top: 0 });
  }

  function handleRegisterDifferent() {
    localStorage.removeItem(STORAGE_KEY);
    setTourist(null);
    window.scrollTo({ top: 0 });
  }

  return (
    <div className="tourist-page">
      {tourist ? (
        <TouristDashboard
          tourist={tourist}
          onRegisterDifferent={handleRegisterDifferent}
        />
      ) : (
        <RegistrationForm onRegistered={handleRegistered} />
      )}
    </div>
  );
}
