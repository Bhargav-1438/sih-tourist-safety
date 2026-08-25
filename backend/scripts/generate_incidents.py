"""Generate a deterministic synthetic incident dataset for the prototype.

SYNTHETIC DATA NOTICE
=====================
This script generates **synthetic** incident data for demonstration and
prototype evaluation only. It does **not** use real personal data, real crime
statistics, or any external data source. All incidents, locations, types, and
timestamps are algorithmically generated.

Demo geography: Vijayawada, Andhra Pradesh, India (approx. 16.4–16.7°N,
80.4–80.7°E) — a plausible tourism-relevant bounding box on the Krishna
river. The dataset intentionally contains spatial clusters (for future DBSCAN
evaluation) plus scattered noise points.

Usage:
    python -m scripts.generate_incidents
"""
import datetime
import random
import sys

# ---------------------------------------------------------------------------
# Demo geography: Vijayawada, Andhra Pradesh, India area
# ---------------------------------------------------------------------------
BOUNDING_BOX = {
    "min_lat": 16.40,
    "max_lat": 16.70,
    "min_lon": 80.40,
    "max_lon": 80.70,
}

# Dense geographic cluster centers (latitude, longitude) — intentionally
# placed within the bounding box to produce visible spatial groups.
CLUSTER_CENTERS = [
    (16.5047, 80.6180),  # Near Vijayawada city centre / Krishna district
    (16.5336, 80.6500),  # Near Kanaka Durgamma temple area
    (16.4740, 80.5500),  # Near Bhavani island / river ghats
    (16.6000, 80.4500),  # Northern edge of the demo area
    (16.4500, 80.6800),  # Eastern edge near Padmavati area
]

# Incident types and severities for variation.
INCIDENT_TYPES = ["theft", "harassment", "medical", "accident",
                  "missing_person", "unsafe_area"]
SEVERITY_RANGE = (1, 5)

# Deterministic seed so repeated runs produce the same dataset.
RANDOM_SEED = 42

# Dataset size.
TOTAL_INCIDENTS = 150
INCIDENTS_PER_CLUSTER = 25  # 5 clusters × 25 = 125 clustered
NOISE_INCIDENTS = TOTAL_INCIDENTS - (len(CLUSTER_CENTERS) * INCIDENTS_PER_CLUSTER)


def _jitter(center: float, rng: random.Random, radius: float = 0.015) -> float:
    """Spread a point within `radius` of `center` (approx. ±1.5 km)."""
    return center + (rng.uniform(-radius, radius))


def generate_incidents(db_session, clear: bool = True) -> dict:
    """Generate and persist the synthetic incident dataset.

    Args:
        db_session: A SQLAlchemy session (SessionLocal).
        clear: If True, delete all existing rows from the incidents table
               before inserting new ones (prevents duplicates on re-runs).

    Returns:
        A summary dict with counts for reporting.
    """
    from app.models.incident import Incident

    rng = random.Random(RANDOM_SEED)

    if clear:
        db_session.execute(Incident.__table__.delete())

    incidents = []
    cluster_count = 0

    # --- Clustered incidents ---
    for cluster_idx, (cx, cy) in enumerate(CLUSTER_CENTERS):
        for _ in range(INCIDENTS_PER_CLUSTER):
            lat = _jitter(cx, rng, radius=0.008)
            lon = _jitter(cy, rng, radius=0.008)
            # Clamp into bounding box.
            lat = min(max(lat, BOUNDING_BOX["min_lat"]), BOUNDING_BOX["max_lat"])
            lon = min(max(lon, BOUNDING_BOX["min_lon"]), BOUNDING_BOX["max_lon"])
            incidents.append(_make_incident(lat, lon, rng))
        cluster_count += 1

    # --- Noise (scattered) incidents ---
    for _ in range(NOISE_INCIDENTS):
        lat = rng.uniform(BOUNDING_BOX["min_lat"], BOUNDING_BOX["max_lat"])
        lon = rng.uniform(BOUNDING_BOX["min_lon"], BOUNDING_BOX["max_lon"])
        incidents.append(_make_incident(lat, lon, rng))

    db_session.add_all(incidents)
    db_session.commit()

    return {
        "generated": len(incidents),
        "clusters": cluster_count,
        "noise": NOISE_INCIDENTS,
        "total": len(incidents),
    }


def _make_incident(lat: float, lon: float, rng: random.Random) -> "Incident":
    """Build a single Incident with a deterministic timestamp and type."""
    import datetime as _dt
    incident_type = rng.choice(INCIDENT_TYPES)
    severity = rng.randint(*SEVERITY_RANGE)
    # Timestamps spread over the past 60 days, deterministic via rng.
    days_ago = rng.randint(0, 59)
    hour = rng.randint(0, 23)
    minute = rng.randint(0, 59)
    occurred = _dt.datetime(2026, 6, 25) + _dt.timedelta(days=days_ago,
                                                          hours=hour,
                                                          minutes=minute)
    return Incident(
        latitude=round(lat, 6),
        longitude=round(lon, 6),
        incident_type=incident_type,
        severity=severity,
        occurred_at=occurred,
    )


def main() -> int:
    """CLI entry point: generate the dataset into the configured SQLite DB."""
    # Import after env setup so config picks up the right DATABASE_URL.
    from app.database import SessionLocal, engine, Base
    from app.models.incident import Incident
    from app.models.tourist import Tourist  # noqa: F401 (registers table)
    from app.models.sos_event import SOSEvent  # noqa: F401 (registers table)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        summary = generate_incidents(db)
    finally:
        db.close()

    print(f"Generated {summary['generated']} synthetic incidents")
    print(f"Clusters: {summary['clusters']}")
    print(f"Noise points: {summary['noise']}")
    print("Note: These are SYNTHETIC incidents for prototype demonstration only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
