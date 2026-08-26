/** Six authority KPI tiles - every value derives from real API responses. */

interface StatCardsProps {
  totalIncidents: number | null;
  totalSos: number | null;
  activeSos: number | null;
  riskZoneCount: number | null;
  criticalHighZones: number | null;
  recommendedUnits: number | null;
  coveragePct: number | null;
}

function formatValue(value: number | null): string {
  return value === null ? "…" : String(value);
}

export default function StatCards(props: StatCardsProps) {
  const tiles: { label: string; value: string; accent?: boolean }[] = [
    { label: "Incidents", value: formatValue(props.totalIncidents) },
    {
      label:
        props.activeSos !== null && props.activeSos > 0
          ? `SOS (${props.activeSos} active)`
          : "SOS events",
      value: formatValue(props.totalSos),
      accent: (props.activeSos ?? 0) > 0,
    },
    { label: "Risk zones", value: formatValue(props.riskZoneCount) },
    {
      label: "Critical / High",
      value: formatValue(props.criticalHighZones),
      accent: (props.criticalHighZones ?? 0) > 0,
    },
    { label: "AI patrols", value: formatValue(props.recommendedUnits) },
    {
      label: "Coverage",
      value:
        props.coveragePct === null ? "…" : `${props.coveragePct.toFixed(1)}%`,
    },
  ];

  return (
    <div className="stat-cards">
      {tiles.map((tile) => (
        <div
          key={tile.label}
          className={`stat-tile ${tile.accent ? "stat-accent" : ""}`}
        >
          <span className="stat-value">{tile.value}</span>
          <span className="stat-label">{tile.label}</span>
        </div>
      ))}
    </div>
  );
}