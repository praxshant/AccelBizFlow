#!/usr/bin/env python
"""
Standalone lead analysis script.
Reproduces all locked baseline metrics from CSV files with assertions.
Run from project root: python analytics/lead_analysis.py
"""
import csv
from pathlib import Path
from collections import defaultdict

DATA_ROOT = Path(__file__).resolve().parent.parent / "YTL_TrackA_Udyam_Digital_Data"


def load_leads():
    with (DATA_ROOT / "smb_leads.csv").open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    rows = load_leads()
    total = len(rows)

    stage_counts = defaultdict(int)
    for row in rows:
        stage_counts[row["stage_reached"]] += 1

    activated = stage_counts.get("Activated", 0)
    conversion = round(activated / total, 4) if total else 0

    print("=" * 60)
    print("ACCEL BIZFLOW - HISTORICAL BASELINE METRICS")
    print("=" * 60)
    print(f"Total leads:          {total:,}")
    print(f"Activations:          {activated:,}")
    print(f"Conversion rate:      {conversion:.2%}")
    print()

    # Segment analysis
    segments = defaultdict(lambda: {"leads": 0, "activated": 0})
    for row in rows:
        seg = row["segment"]
        segments[seg]["leads"] += 1
        if row["stage_reached"] == "Activated":
            segments[seg]["activated"] += 1

    print("Segment Breakdown:")
    for seg, data in sorted(segments.items()):
        conv = round(data["activated"] / data["leads"], 4) if data["leads"] else 0
        print(f"  {seg:<35} leads={data['leads']:,}  activated={data['activated']:,}  conv={conv:.2%}")

    print()

    # Assertions against locked baseline
    assert total == 5000, f"Expected 5000 leads, got {total}"
    assert activated == 368, f"Expected 368 activations, got {activated}"
    assert abs(conversion - 0.0736) < 0.001, f"Conversion rate mismatch: {conversion}"

    assert segments["Micro retail & services"]["leads"] == 2709, \
        f"Micro retail leads mismatch: {segments['Micro retail & services']['leads']}"
    assert segments["Professional offices"]["leads"] == 1247, \
        f"Professional offices leads mismatch: {segments['Professional offices']['leads']}"

    print("[PASS] All baseline metric assertions passed.")


if __name__ == "__main__":
    main()
