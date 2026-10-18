"""Simulated hospital scenarios for testing MediMesh end to end.

This is synthetic data with a simple, documented structure. It is meant for
repeatable stress tests (busy ER, reduced staffing, flu surge), not as a
substitute for the real dataset.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .schema import DEFAULT_SCHEMA, Schema

SCENARIO_DESCRIPTIONS = {
    "baseline": "Typical week: daytime peak, quieter nights and weekends.",
    "busy_er": "Evening rush: arrivals 60% above normal from 16:00 to 23:59.",
    "reduced_staffing": "Staffing cut to 70% of the normal schedule.",
    "flu_surge": "Arrivals ramp up to +50% over the second half of the period.",
}


def generate_hospital_data(
    days: int = 60,
    scenario: str = "baseline",
    seed: int = 0,
    start: str = "2026-01-05",
    schema: Schema = DEFAULT_SCHEMA,
) -> pd.DataFrame:
    """Hourly synthetic hospital data for one scenario."""
    if scenario not in SCENARIO_DESCRIPTIONS:
        raise ValueError(f"unknown scenario {scenario!r}; choose from {sorted(SCENARIO_DESCRIPTIONS)}")

    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=days * 24, freq="h")
    n = len(idx)
    hour, dow = idx.hour.to_numpy(), idx.dayofweek.to_numpy()

    daily = 1 + 0.45 * np.sin((hour - 9) / 24 * 2 * np.pi)          # peaks mid-afternoon
    weekly = np.where(dow == 0, 1.1, np.where(dow >= 5, 0.95, 1.0))
    mult = np.ones(n)
    staff_mult = 1.0
    if scenario == "busy_er":
        mult[hour >= 16] *= 1.6
    elif scenario == "reduced_staffing":
        staff_mult = 0.7
    elif scenario == "flu_surge":
        ramp = np.clip((np.arange(n) - 0.5 * n) / (0.25 * n), 0, 1)
        mult *= 1 + 0.5 * ramp

    volume = rng.poisson(20 * daily * weekly * mult).astype(float)

    shift_staff = np.where((hour >= 7) & (hour < 15), 10, np.where((hour >= 15) & (hour < 23), 9, 5))
    staff = np.round(shift_staff * staff_mult) - rng.binomial(1, 0.1, n)  # occasional absence
    staff = np.maximum(staff, 1).astype(float)

    load = volume / staff                                             # patients per staff member
    wait = 15 + 25 * np.maximum(0, load - 2.5) ** 1.3 + rng.normal(0, 4, n)
    wait = np.maximum(wait, 2)

    target = 50 + 8 * load
    noise = rng.normal(0, 1.5, n)
    occ = np.empty(n)
    occ[0] = 60
    for i in range(1, n):
        occ[i] = 0.9 * occ[i - 1] + 0.1 * target[i] + noise[i]
    occ = np.clip(occ, 5, 100)

    return pd.DataFrame(
        {
            schema.timestamp: idx,
            schema.patient_volume: volume,
            schema.staff_on_duty: staff,
            schema.wait_time: wait.round(1),
            schema.bed_occupancy: occ.round(1),
        }
    )
