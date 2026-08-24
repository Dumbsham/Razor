"""Generate the locked PaySim split summary without writing a duplicate dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.ingestion import (
    build_split_summary,
    load_transactions,
    split_transactions,
    write_split_summary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="Paysim.csv", help="Path to the PaySim CSV")
    parser.add_argument(
        "--output",
        default="data/processed/ingestion_summary.json",
        help="Path for the generated summary JSON",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    transactions = load_transactions(args.input)
    summary = build_split_summary(split_transactions(transactions))
    output_path = write_split_summary(summary, args.output)
    print(f"Wrote split summary: {Path(output_path)}")
    for name, values in summary["splits"].items():
        print(
            f"{name}: {values['row_count']:,} rows, "
            f"{values['fraud_count']:,} fraud labels, "
            f"{values['fraud_rate']:.4%} fraud rate"
        )


if __name__ == "__main__":
    main()
