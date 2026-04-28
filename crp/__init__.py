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
from .rankings import (
    compute_player_rankings,
    plot_top_receivers,
    plot_pressure_specialists,
    load_play_targets,
)
from .animation import animate_play

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
    "compute_player_rankings",
    "plot_top_receivers",
    "plot_pressure_specialists",
    "load_play_targets",
    "animate_play",
]
