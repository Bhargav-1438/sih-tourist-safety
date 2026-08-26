/** Tourist registration form - mirrors backend TouristCreate schema. */
import { useState, type FormEvent } from "react";
import { registerTourist } from "../../api/tourist";
import type { Tourist } from "../../types/tourist";

// Same rule the backend enforces: 10 digits, first digit 6-9.
const PHONE_PATTERN = /^[6-9]\d{9}$/;

function normalizePhone(raw: string): string {
  const cleaned = raw.replace(/[\s\-()]/g, "");
  if (cleaned.startsWith("+91")) return cleaned.slice(3);
  if (cleaned.startsWith("91") && cleaned.length > 10) return cleaned.slice(2);
  return cleaned;
}

interface RegistrationFormProps {
  onRegistered: (tourist: Tourist) => void;
}

export default function RegistrationForm({ onRegistered }: RegistrationFormProps) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Please enter your full name.");
      return;
    }
    const normalizedPhone = normalizePhone(phone);
    if (!PHONE_PATTERN.test(normalizedPhone)) {
      setError(
        "Enter a valid Indian mobile number (10 digits, starting with 6-9).",
      );
      return;
    }

    setSubmitting(true);
    try {
      // The backend is authoritative: it re-validates and normalizes.
      const tourist = await registerTourist({
        name: trimmedName,
        phone: normalizedPhone,
      });
      onRegistered(tourist);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Registration failed. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="tourist-card registration-card">
      <h2>Register</h2>
      <p className="muted">
        Create your prototype tourist profile to unlock safety features.
      </p>

      <form onSubmit={handleSubmit} noValidate>
        <label htmlFor="tourist-name">
          Full name <span aria-hidden="true">*</span>
        </label>
        <input
          id="tourist-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Rahul Kumar"
          autoComplete="name"
          maxLength={255}
          required
        />

        <label htmlFor="tourist-phone">
          Mobile number <span aria-hidden="true">*</span>
        </label>
        <input
          id="tourist-phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="9876543210"
          inputMode="tel"
          autoComplete="tel"
          maxLength={20}
          required
        />
        <p className="field-hint">Indian 10-digit mobile number.</p>

        {error && (
          <p role="alert" className="form-error">
            {error}
          </p>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting || !name.trim() || !phone.trim()}
        >
          {submitting ? "Registering…" : "Register"}
        </button>
      </form>
    </section>
  );
}