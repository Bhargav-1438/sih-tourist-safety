"""Greedy p-median / weighted-coverage patrol optimization (Prompt 6).

Consumes the risk zones produced by app.risk_engine.compute_risk_zones() and
recommends patrol locations. Pure computation: no routing APIs, no road
networks, no persistence.

Algorithm (viva summary):
  * Candidate sites are the risk-zone centers themselves.
  * Zone weight w_z = risk_score (0-100) - already fuses density, severity,
    and incident-type variety from Prompt 5.
  * A patrol at candidate c covers every zone whose center lies within
    service_radius_km R of c (haversine ground distance). A candidate always
    covers its own zone (distance 0), so no placement is ever wasted.
  * Greedy loop: repeatedly place the candidate with the largest total
    uncovered weight inside R (classic p-median greedy heuristic). Ties break
    to the first candidate in the engine's deterministic (-risk_score,
    latitude, longitude) ordering, i.e. southern/western wins.
"""
import datetime

from app.risk_engine import haversine_km

ALGORITHM_NAME = "greedy_pmedian_weighted_coverage"

# Band order used to report the highest severity level among served zones.
_LEVEL_ORDER = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def optimize_patrols(
    zones: list[dict], num_units: int, service_radius_km: float
) -> dict:
    """Return the PatrolPlanResponse payload dict for the given zones.

    ``zones`` must use the exact dict shape produced by the Prompt 5 engine.
    """
    total_weight = sum(z["risk_score"] for z in zones)
    envelope = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc),
        "algorithm": ALGORITHM_NAME,
        "requested_units": num_units,
        "placed_units": 0,
        "service_radius_km": service_radius_km,
        "total_zones": len(zones),
        "total_weight": total_weight,
        "covered_weight": 0,
        "coverage_pct": 0.0,
        "patrols": [],
        "uncovered_zones": [],
    }
    if not zones or num_units <= 0:
        return envelope

    unassigned = {z["zone_id"]: z for z in zones}
    host_ids: set[int] = set()

    while num_units > 0 and unassigned:
        best_candidate = None
        best_gain = -1
        best_served: list[dict] = []
        for candidate in zones:  # engine order is already deterministic
            cid = candidate["zone_id"]
            if cid in host_ids:
                continue
            served = [
                z
                for z in unassigned.values()
                if haversine_km(
                    candidate["center_latitude"], candidate["center_longitude"],
                    z["center_latitude"], z["center_longitude"],
                )
                <= service_radius_km
            ]
            gain = sum(z["risk_score"] for z in served)
            if gain > best_gain:
                best_candidate, best_gain, best_served = candidate, gain, served

        if best_candidate is None:  # defensive: every center hosts a patrol
            break

        distances = [
            haversine_km(
                best_candidate["center_latitude"], best_candidate["center_longitude"],
                z["center_latitude"], z["center_longitude"],
            )
            for z in best_served
        ]
        covered_w = sum(z["risk_score"] for z in best_served)
        top_level = max(
            (z["risk_level"] for z in best_served), key=_LEVEL_ORDER.__getitem__
        )
        envelope["patrols"].append(
            {
                "unit_id": len(envelope["patrols"]) + 1,
                "latitude": best_candidate["center_latitude"],
                "longitude": best_candidate["center_longitude"],
                "covers_zone_ids": sorted(z["zone_id"] for z in best_served),
                "covered_zone_count": len(best_served),
                "covered_weight": covered_w,
                "coverage_share_pct": (
                    round(100.0 * covered_w / total_weight, 2) if total_weight else 0.0
                ),
                "avg_zone_distance_km": (
                    round(sum(distances) / len(distances), 3) if distances else 0.0
                ),
                "highest_risk_level": top_level,
            }
        )
        host_ids.add(best_candidate["zone_id"])
        for z in best_served:
            del unassigned[z["zone_id"]]
        num_units -= 1

    envelope["placed_units"] = len(envelope["patrols"])
    uncovered_weight = sum(z["risk_score"] for z in unassigned.values())
    covered_total = total_weight - uncovered_weight
    envelope["covered_weight"] = covered_total
    envelope["coverage_pct"] = (
        round(100.0 * covered_total / total_weight, 2) if total_weight else 0.0
    )
    envelope["uncovered_zones"] = [
        {
            "zone_id": z["zone_id"],
            "risk_score": z["risk_score"],
            "risk_level": z["risk_level"],
            "center_latitude": z["center_latitude"],
            "center_longitude": z["center_longitude"],
        }
        for z in sorted(
            unassigned.values(), key=lambda z: (-z["risk_score"], z["zone_id"])
        )
    ]
    return envelope