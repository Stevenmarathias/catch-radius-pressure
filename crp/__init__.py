"""
Catch Radius Pressure (CRP) — NFL Big Data Bowl 2026
"""

from .metric import (
    compute_crp_for_play,
    compute_crp_dataset,
    crp_label,
    add_crp_labels,
    CATCH_RADIUS_YDS,
)
from .data_loader import (
    load_week,
    load_all_weeks,
    load_supplementary,
    merge_crp_with_supplementary,
    get_play_snapshot,
)

__all__ = [
    "compute_crp_for_play",
    "compute_crp_dataset",
    "crp_label",
    "add_crp_labels",
    "CATCH_RADIUS_YDS",
    "load_week",
    "load_all_weeks",
    "load_supplementary",
    "merge_crp_with_supplementary",
    "get_play_snapshot",
]
