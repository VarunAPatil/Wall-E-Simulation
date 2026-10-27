#!/usr/bin/env python3
"""Plot the unloaded and 15 pF ESD-proxy openEMS runs together."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "devkitc1_usb"


def main() -> None:
    bare = np.genfromtxt(RESULTS / "bare" / "sparams.csv",
                         delimiter=",", names=True)
    loaded = np.genfromtxt(RESULTS / "esd15pf" / "sparams.csv",
                           delimiter=",", names=True)
    fig, (ax21, ax11) = plt.subplots(2, 1, figsize=(9, 7), sharex=True,
                                     layout="constrained")
    for data, name, color in ((bare, "Ideal unloaded pair", "#2563eb"),
                              (loaded, "15 pF shunt per line", "#e87722")):
        freq_ghz = data["frequency_hz"]/1e9
        ax21.plot(freq_ghz, data["Sdd21_dB"], label=name, color=color)
        ax11.plot(freq_ghz, data["Sdd11_dB"], label=name, color=color)
    ax21.set_ylabel("Sdd21 transmission (dB)")
    ax11.set(xlabel="Frequency (GHz)", ylabel="Sdd11 reflection (dB)")
    for ax in (ax21, ax11):
        ax.grid(alpha=0.3)
        ax.legend()
    fig.suptitle("Assumed ESP32-S3-DevKitC-1 native USB path: ESD capacitance proxy")
    out = RESULTS / "comparison.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
