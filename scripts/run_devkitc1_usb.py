#!/usr/bin/env python3
"""Simulate an idealized ESP32-S3-DevKitC-1 native-USB trace section.

This is a passive PCB interconnect model, not a circuit or SoC model. The
schematic establishes USB_DN/GPIO19 and USB_DP/GPIO20; trace dimensions and
the four-layer-style 0.20 mm reference-plane spacing are explicit assumptions.

Run from simulations/ with:
    ./scripts/run_devkitc1_usb.sh
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from CSXCAD import ContinuousStructure
from openEMS import openEMS


ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
RESULTS = ROOT / "results" / "devkitc1_usb"

# Millimetres throughout the geometry. These are illustrative dimensions;
# Espressif's published schematic does not provide this routing or stackup.
TRACE_START = 1.0
TRACE_END = 11.0
TRACE_WIDTH = 0.25
TRACE_GAP = 0.20
PAD_START = 4.0
PAD_END = 4.8
PAD_WIDTH = 0.35
PLANE_SPACING = 0.20
FR4_ER = 4.2
PORT_RESISTANCE = 50.0  # two 50-ohm single-ended ports = 100-ohm differential reference
F_MAX = 1.5e9


def add_2d_box(prop, x0, x1, y0, y1, z, priority=10):
    prop.AddBox([x0, y0, z], [x1, y1, z], priority=priority)


def draw_geometry(path: Path, esd_cap_pf: float = 0) -> None:
    fig, ax = plt.subplots(figsize=(11, 4.2), layout="constrained")
    ax.add_patch(plt.Rectangle((0, -0.85), 12, 1.7, fc="#e9d5a8", ec="#7c623d", lw=1.5))
    for name, y0, color in (("D− / GPIO19", -0.35, "#2563eb"),
                            ("D+ / GPIO20", 0.10, "#db2777")):
        ax.add_patch(plt.Rectangle((TRACE_START, y0), TRACE_END-TRACE_START,
                                   TRACE_WIDTH, fc=color, ec="#111827", lw=0.8))
        pad_y0 = (y0 + TRACE_WIDTH/2) - PAD_WIDTH/2
        ax.add_patch(plt.Rectangle((PAD_START, pad_y0), PAD_END-PAD_START,
                                   PAD_WIDTH, fc=color, ec="#111827", lw=0.8))
        ax.text(TRACE_END+0.12, y0+TRACE_WIDTH/2, name, va="center", fontsize=10)
        ax.scatter([TRACE_START+0.05, TRACE_END-0.05], [y0+TRACE_WIDTH/2]*2,
                   s=30, c="white", edgecolors="#111827", zorder=5)
        if esd_cap_pf:
            ax.scatter([4.45], [y0+TRACE_WIDTH/2], marker="x", s=55,
                       c="#111827", linewidths=1.6, zorder=6)
    ax.annotate("connector-side ports", (1.05, 0.35), (0.15, 0.77),
                arrowprops={"arrowstyle":"->"}, fontsize=9)
    ax.annotate("module-side ports", (10.95, 0.35), (8.6, 0.77),
                arrowprops={"arrowstyle":"->"}, fontsize=9)
    ax.annotate("widened pad proxy", (4.4, -0.35), (3.2, -0.72),
                arrowprops={"arrowstyle":"->"}, fontsize=9)
    if esd_cap_pf:
        ax.text(5.0, 0.69, f"X = {esd_cap_pf:g} pF to ground per line", fontsize=9)
    ax.set(xlim=(-0.2, 13.6), ylim=(-1.0, 1.05), xlabel="x (mm)", ylabel="y (mm)",
           title="DevKitC-1 native USB: assumed passive trace section (top view)")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def draw_3d_geometry(path: Path, esd_cap_pf: float = 0) -> None:
    fig = plt.figure(figsize=(10, 5.4), layout="constrained")
    ax = fig.add_subplot(111, projection="3d")

    def surface(x0, x1, y0, y1, z, color, alpha=1.0):
        corners = [(x0, y0, z), (x1, y0, z),
                   (x1, y1, z), (x0, y1, z)]
        ax.add_collection3d(Poly3DCollection([corners], facecolors=color,
                                              edgecolors="#334155", linewidths=0.5,
                                              alpha=alpha))

    surface(0, 12, -0.85, 0.85, 0, "#64748b")
    surface(0, 12, -0.85, 0.85, PLANE_SPACING, "#e9d5a8", 0.65)
    for y0, color in ((-0.35, "#2563eb"), (0.10, "#db2777")):
        surface(TRACE_START, TRACE_END, y0, y0+TRACE_WIDTH,
                PLANE_SPACING+0.005, color)
        pad_y0 = y0 + TRACE_WIDTH/2 - PAD_WIDTH/2
        surface(PAD_START, PAD_END, pad_y0, pad_y0+PAD_WIDTH,
                PLANE_SPACING+0.01, color)
        if esd_cap_pf:
            ax.plot([4.45, 4.45], [y0+TRACE_WIDTH/2]*2,
                    [0, PLANE_SPACING], color="#111827", lw=2)
    ax.set(xlim=(0, 12), ylim=(-0.9, 0.9), zlim=(0, 0.35),
           xlabel="x (mm)", ylabel="y (mm)", zlabel="z (mm)",
           title="Assumed USB pair, FR-4 layer and ideal ground plane")
    ax.set_box_aspect((12, 2.4, 1.7))  # vertical dimension enlarged for legibility
    ax.view_init(elev=30, azim=-65)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_results(csv_file: Path, plot: Path, title: str) -> None:
    data = np.genfromtxt(csv_file, delimiter=",", names=True)
    ghz = data["frequency_hz"] / 1e9
    fig, (upper, lower) = plt.subplots(2, 1, figsize=(9, 7),
                                       sharex=True, layout="constrained")
    upper.plot(ghz, data["Sdd21_dB"], color="#e87722")
    upper.set_ylabel("Sdd21 (dB)")
    upper.grid(alpha=0.3)
    lower.plot(ghz, data["Sdd11_dB"], label="Sdd11: reflection")
    lower.plot(ghz, data["output_common_over_input_diff_voltage_dB"],
               label="Output common / input diff voltage", ls="--")
    lower.set(xlabel="Frequency (GHz)", ylabel="Magnitude (dB)")
    lower.grid(alpha=0.3)
    lower.legend(loc="best")
    fig.suptitle(title)
    fig.savefig(plot, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="devkitc1_usb", help="identifier for output files")
    parser.add_argument("--max-steps", type=int, default=100000)
    parser.add_argument("--esd-cap-pf", type=float, default=0.0,
                        help="linear shunt capacitance per USB line in pF; 15 models the schematic's D8/D9 small-signal value")
    args = parser.parse_args()
    if not args.case.isidentifier() or args.max_steps <= 0 or args.esd_cap_pf < 0:
        parser.error("case must be an identifier; max-steps positive; ESD capacitance nonnegative")

    MODELS.mkdir(exist_ok=True)
    if args.case in ("devkitc1_usb", "devkitc1_usb_esd15pf"):
        case_name = "bare" if args.esd_cap_pf == 0 else f"esd{args.esd_cap_pf:g}pf"
    else:
        case_name = args.case
    case_dir = RESULTS / case_name
    case_dir.mkdir(parents=True, exist_ok=True)
    run_dir = case_dir / "raw"
    run_dir.mkdir(exist_ok=True)

    fdtd = openEMS(NrTS=args.max_steps, EndCriteria=1e-5)
    # The broader pulse reaches the 1.5 GHz reporting band while finishing
    # early enough to leave several pulse lengths for the fields to decay.
    fdtd.SetGaussExcite(F_MAX, F_MAX)
    fdtd.SetBoundaryCond(["PML_8", "PML_8", "PML_8", "PML_8", "PEC", "PML_8"])
    csx = ContinuousStructure()
    fdtd.SetCSX(csx)
    mesh = csx.GetGrid()
    mesh.SetDeltaUnit(1e-3)
    # 0.10 mm longitudinal, 0.05 mm lateral and 0.04 mm vertical cells.
    # A 0.20 mm gap has four lateral cells; the 0.20 mm dielectric has five.
    mesh.AddLine("x", np.round(np.arange(-1.5, 13.5+0.05, 0.1), 5))
    mesh.AddLine("y", np.round(np.arange(-2.5, 2.5+0.025, 0.05), 5))
    mesh.AddLine("z", np.round(np.arange(0, 1.2+0.02, 0.04), 5))

    fr4 = csx.AddMaterial("assumed_FR4", epsilon=FR4_ER)
    fr4.AddBox([-1.5, -2.5, 0], [13.5, 2.5, PLANE_SPACING], priority=1)
    ground = csx.AddMetal("ideal_ground_plane")
    add_2d_box(ground, -1.5, 13.5, -2.5, 2.5, 0, priority=5)
    copper = csx.AddMetal("ideal_top_copper")

    traces = (("D_minus_GPIO19", -0.35, -1.0),
              ("D_plus_GPIO20", 0.10, +1.0))
    ports = {}
    for idx, (name, y0, polarity) in enumerate(traces):
        y1 = y0 + TRACE_WIDTH
        add_2d_box(copper, TRACE_START, TRACE_END, y0, y1, PLANE_SPACING)
        pad_y0 = y0 + TRACE_WIDTH/2 - PAD_WIDTH/2
        add_2d_box(copper, PAD_START, PAD_END, pad_y0,
                   pad_y0+PAD_WIDTH, PLANE_SPACING, priority=11)
        # Each signal has a 50-ohm source or load to the ground plane. Equal
        # and opposite sources launch the USB pair's differential mode.
        ports[name + "_in"] = fdtd.AddLumpedPort(
            1+idx, PORT_RESISTANCE,
            [TRACE_START, y0, 0], [TRACE_START+0.1, y1, PLANE_SPACING],
            "z", excite=polarity, priority=20)
        ports[name + "_out"] = fdtd.AddLumpedPort(
            3+idx, PORT_RESISTANCE,
            [TRACE_END-0.1, y0, 0], [TRACE_END, y1, PLANE_SPACING],
            "z", excite=0, priority=20)

    if args.esd_cap_pf:
        esd = csx.AddLumpedElement("D8_D9_linear_capacitance_proxy", ny="z",
                                   C=args.esd_cap_pf*1e-12, caps=True)
        for _, y0, _ in traces:
            center_y = y0 + TRACE_WIDTH/2
            esd.AddBox([4.4, center_y-0.05, 0],
                       [4.5, center_y+0.05, PLANE_SPACING], priority=21)

    model = MODELS / f"{args.case}.xml"
    geometry = case_dir / "geometry.png"
    geometry_3d = case_dir / "geometry_3d.png"
    csx.Write2XML(str(model))
    draw_geometry(geometry, args.esd_cap_pf)
    draw_3d_geometry(geometry_3d, args.esd_cap_pf)
    print(f"Saved {model.relative_to(ROOT)}", flush=True)
    print(f"Saved {geometry.relative_to(ROOT)}", flush=True)
    print(f"Saved {geometry_3d.relative_to(ROOT)}", flush=True)
    print(f"Running {args.case}: 10 mm differential pair; "
          f"{args.esd_cap_pf:g} pF ESD proxy per line; max {args.max_steps} steps", flush=True)
    fdtd.Run(str(run_dir), cleanup=True)

    freq = np.linspace(10e6, F_MAX, 300)
    for port in ports.values():
        port.CalcPort(str(run_dir), freq, ref_impedance=PORT_RESISTANCE)
    dn_in = ports["D_minus_GPIO19_in"]
    dp_in = ports["D_plus_GPIO20_in"]
    dn_out = ports["D_minus_GPIO19_out"]
    dp_out = ports["D_plus_GPIO20_out"]
    incident_diff = dp_in.uf_inc - dn_in.uf_inc
    sdd11 = (dp_in.uf_ref - dn_in.uf_ref) / incident_diff
    sdd21 = (dp_out.uf_ref - dn_out.uf_ref) / incident_diff
    # This is a voltage ratio, not a power-normalized mixed-mode S parameter.
    common_over_diff = (dp_out.uf_ref + dn_out.uf_ref) / incident_diff

    def db(value):
        return 20*np.log10(np.maximum(np.abs(value), 1e-12))

    csv_file = case_dir / "sparams.csv"
    with csv_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frequency_hz", "Sdd11_dB", "Sdd21_dB",
                         "output_common_over_input_diff_voltage_dB"])
        writer.writerows(zip(freq, db(sdd11), db(sdd21), db(common_over_diff)))

    plot = case_dir / "sparams.png"
    plot_results(csv_file, plot, f"Assumed DevKitC-1 USB pair · {args.esd_cap_pf:g} pF per line")
    print(f"Saved {csv_file.relative_to(ROOT)}", flush=True)
    print(f"Saved {plot.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
