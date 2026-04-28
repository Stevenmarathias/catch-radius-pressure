"""
scripts/compute_crp.py
======================
Recompute CRP for all 18 weeks and save to data/.

Usage:
    python scripts/compute_crp.py --data_dir /path/to/competition/data
    python scripts/compute_crp.py  # uses default data/ symlink
"""

import argparse
import os
import sys
import glob
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from crp.metric import compute_crp_dataset, add_crp_labels


def main():
    parser = argparse.ArgumentParser(description="Compute CRP for all weeks")
    parser.add_argument(
        "--data_dir",
        default=os.path.join(
            os.path.dirname(__file__), "..", "data",
            "114239_nfl_competition_files_published_analytics_final"
        ),
        help="Path to competition data root",
    )
    parser.add_argument("--season", type=int, default=2023)
    parser.add_argument("--weeks", nargs="+", type=int, default=list(range(1, 19)))
    parser.add_argument("--output_dir", default=None)
    args = parser.parse_args()

    data_dir = os.path.abspath(args.data_dir)
    output_dir = args.output_dir or os.path.join(
        os.path.dirname(__file__), "..", "data"
    )
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.isdir(data_dir):
        print(f"ERROR: Data directory not found: {data_dir}")
        sys.exit(1)

    print(f"Data root: {data_dir}")
    print(f"Output:    {output_dir}")
    print(f"Weeks:     {args.weeks}\n")

    all_crp = []

    for w in args.weeks:
        input_path  = os.path.join(data_dir, "train", f"input_{args.season}_w{w:02d}.csv")
        output_path = os.path.join(data_dir, "train", f"output_{args.season}_w{w:02d}.csv")

        if not os.path.isfile(input_path):
            print(f"  Week {w:02d} — input file not found, skipping")
            continue

        df_in  = pd.read_csv(input_path, low_memory=False)
        df_out = pd.read_csv(output_path)
        df_crp = compute_crp_dataset(df_in, df_out)
        df_crp["week"] = w

        week_path = os.path.join(output_dir, f"crp_w{w:02d}.csv")
        df_crp.to_csv(week_path, index=False)
        all_crp.append(df_crp)
        print(f"  Week {w:02d}: {len(df_crp):>4} plays → {week_path}")

    if not all_crp:
        print("No data processed.")
        return

    full = pd.concat(all_crp, ignore_index=True)
    full = add_crp_labels(full)
    all_path = os.path.join(output_dir, "crp_all_weeks.csv")
    full.to_csv(all_path, index=False)
    print(f"\n✓ Full season ({len(full):,} plays) → {all_path}")
    print(full["crp"].describe().round(4))
    print(full["crp_label"].value_counts())


if __name__ == "__main__":
    main()
