"""
Data loading utilities for the NFL Big Data Bowl 2026 CRP project.
"""

import os
import glob
import pandas as pd
from typing import Optional, List, Tuple


DATA_ROOT = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "114239_nfl_competition_files_published_analytics_final",
)


def _find_data_root(data_dir: Optional[str] = None) -> str:
    """Locate the competition data root directory."""
    if data_dir:
        return data_dir
    if os.path.isdir(DATA_ROOT):
        return DATA_ROOT
    raise FileNotFoundError(
        "Could not find competition data. Pass data_dir= explicitly, "
        "or symlink/copy the data folder to data/114239_nfl_competition_files_published_analytics_final/"
    )


def load_week(
    week: int,
    season: int = 2023,
    data_dir: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load input and output tracking data for a single week.

    Returns
    -------
    (df_input, df_output) tuple of DataFrames
    """
    root = _find_data_root(data_dir)
    week_str = f"w{week:02d}"
    input_path = os.path.join(root, "train", f"input_{season}_{week_str}.csv")
    output_path = os.path.join(root, "train", f"output_{season}_{week_str}.csv")

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not os.path.isfile(output_path):
        raise FileNotFoundError(f"Output file not found: {output_path}")

    df_in = pd.read_csv(input_path, low_memory=False)
    df_out = pd.read_csv(output_path)
    return df_in, df_out


def load_all_weeks(
    season: int = 2023,
    weeks: Optional[List[int]] = None,
    data_dir: Optional[str] = None,
    verbose: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and concatenate input/output data across all (or selected) weeks.

    Parameters
    ----------
    season : int
    weeks  : list of week numbers to load; None = all available weeks
    data_dir : path override
    verbose  : print progress

    Returns
    -------
    (df_input, df_output) concatenated DataFrames
    """
    root = _find_data_root(data_dir)
    train_dir = os.path.join(root, "train")

    if weeks is None:
        input_files = sorted(glob.glob(os.path.join(train_dir, f"input_{season}_w*.csv")))
        weeks = [
            int(os.path.basename(f).split("_w")[1].replace(".csv", ""))
            for f in input_files
        ]

    all_inputs, all_outputs = [], []
    for w in weeks:
        if verbose:
            print(f"  Loading week {w:02d}...", end=" ")
        df_in, df_out = load_week(w, season=season, data_dir=data_dir)
        all_inputs.append(df_in)
        all_outputs.append(df_out)
        if verbose:
            plays = df_in["play_id"].nunique()
            print(f"{plays} plays")

    df_input = pd.concat(all_inputs, ignore_index=True)
    df_output = pd.concat(all_outputs, ignore_index=True)

    if verbose:
        total = df_input.groupby(["game_id", "play_id"]).ngroups
        print(f"\n✓ Loaded {total:,} total plays across {len(weeks)} weeks.")

    return df_input, df_output


def load_supplementary(data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load supplementary play-level metadata (formations, coverage, EPA, etc.).
    """
    root = _find_data_root(data_dir)
    path = os.path.join(root, "supplementary_data.csv")
    df = pd.read_csv(path, low_memory=False)
    return df


def merge_crp_with_supplementary(
    df_crp: pd.DataFrame,
    df_supp: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join CRP results with supplementary play metadata.

    Parameters
    ----------
    df_crp  : output of compute_crp_dataset()
    df_supp : output of load_supplementary()

    Returns
    -------
    Merged DataFrame
    """
    merged = df_crp.merge(
        df_supp,
        on=["game_id", "play_id"],
        how="left",
    )
    return merged


def get_play_snapshot(
    df_input: pd.DataFrame,
    game_id: int,
    play_id: int,
    frame: str = "last",
) -> pd.DataFrame:
    """
    Extract all player positions for a single play at a specific frame.

    Parameters
    ----------
    df_input : full input DataFrame
    game_id, play_id : identifiers
    frame : 'last' (ball release) | 'first' | int frame_id

    Returns
    -------
    DataFrame with one row per player
    """
    play = df_input[(df_input["game_id"] == game_id) & (df_input["play_id"] == play_id)]
    if play.empty:
        raise ValueError(f"Play ({game_id}, {play_id}) not found.")

    if frame == "last":
        fid = play["frame_id"].max()
    elif frame == "first":
        fid = play["frame_id"].min()
    else:
        fid = int(frame)

    return play[play["frame_id"] == fid].copy()
