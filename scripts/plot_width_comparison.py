#!/usr/bin/env python3
"""Compare the separately saved 3 mm and 4 mm microstrip runs."""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "microstrip"


def load(case):
    with (RESULTS / case / "sparams.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        key: [float(row[key]) for row in rows]
        for key in ("frequency_hz", "S11_dB", "S21_dB")
    }


def main():
    cases = (("3 mm trace", load("3mm")),
             ("4 mm trace", load("4mm")))
    wide = cases[1][1]
    wide_fig, wide_axis = plt.subplots(figsize=(8.2, 4.8), layout="constrained")
    wide_axis.plot([f / 1e9 for f in wide["frequency_hz"]], wide["S11_dB"],
                   label="S11: reflected")
    wide_axis.plot([f / 1e9 for f in wide["frequency_hz"]], wide["S21_dB"],
                   label="S21: transmitted")
    wide_axis.set(xlabel="Frequency (GHz)", ylabel="Magnitude (dB)",
                  title="20 mm, 4 mm wide microstrip over an ideal ground plane")
    wide_axis.set_ylim(-60, max(3, max(wide["S21_dB"]) + 1))
    wide_axis.grid(True, alpha=0.35)
    wide_axis.legend()
    wide_output = RESULTS / "4mm" / "sparams.png"
    wide_fig.savefig(wide_output, dpi=160)
    plt.close(wide_fig)

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True,
                             layout="constrained")
    for axis, (key, title) in zip(axes, (("S11_dB", "S11: reflection"),
                                         ("S21_dB", "S21: transmission"))):
        for label, data in cases:
            axis.plot([f / 1e9 for f in data["frequency_hz"]], data[key],
                      label=label, linewidth=1.2)
        axis.set(title=title, ylabel="Magnitude (dB)", xlim=(0, 2))
        axis.grid(True, alpha=0.3)
        axis.legend()
    axes[-1].set_xlabel("Frequency (GHz)")
    fig.suptitle("Microstrip width comparison; same substrate, mesh limit and timestep cap")
    output = RESULTS / "width_comparison.png"
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(f"Saved {wide_output.relative_to(ROOT)}")
    print(f"Saved {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
