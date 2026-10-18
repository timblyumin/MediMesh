"""Column names used across the MediMesh ML modules.

If the real dataset uses different column names, change them here (or build a
``Schema(...)`` with your names) instead of editing every module.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Schema:
    timestamp: str = "timestamp"
    wait_time: str = "ed_wait_minutes"
    bed_occupancy: str = "bed_occupancy_pct"
    patient_volume: str = "patient_volume"  # patient arrivals per hour
    staff_on_duty: str = "staff_on_duty"

    @property
    def numeric_columns(self) -> list[str]:
        return [self.wait_time, self.bed_occupancy, self.patient_volume, self.staff_on_duty]


DEFAULT_SCHEMA = Schema()
