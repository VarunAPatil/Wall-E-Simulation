#!/usr/bin/env python3
"""A first PCB field simulation: one microstrip trace over a ground plane.

Run from simulations/ after openEMS has been built:
    ./scripts/run.sh
    ./scripts/run.sh --trace-width-um 4000 --case microstrip_4mm

The model is intentionally small. It has one trace, one dielectric, one
reference plane, and two ports. It does not import the full SRA board.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from CSXCAD import ContinuousStructure
from openEMS import openEMS


ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models"
RESULT_DIR = ROOT / "results" / "microstrip"

# These are the model inputs. Distances are in micrometres because the
# coordinate unit below is one micrometre.
LINE_LENGTH_UM = 20_000       # 20 mm from port to port
TRACE_WIDTH_UM = 3_000        # about 50 ohms for the assumed stackup
SUBSTRATE_HEIGHT_UM = 1_600   # 1.6 mm board thickness
SUBSTRATE_ER = 4.2            # assumed FR-4 relative permittivity
MAX_FREQUENCY_HZ = 2.0e9
MAX_MESH_CELL_UM = 200
MAX_TIMESTEPS = 300_000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-width-um", type=int, default=TRACE_WIDTH_UM)
    parser.add_argument("--case", default="microstrip",
                        help="name used for this case's model and result files")
    args = parser.parse_args()
    if args.trace_width_um <= 0 or not args.case.isidentifier():
        parser.error("trace width must be positive and case must be an identifier")

    case_name = (f"{args.trace_width_um/1000:g}mm"
                 if args.case in ("microstrip", "microstrip_4mm") else args.case)
    case_dir = RESULT_DIR / case_name
    run_dir = case_dir / "raw"
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    # FDTD = the time-domain field solver. A short Gaussian pulse contains a
    # range of frequencies; we later calculate the response across that band.
    # The idealized model has no material losses, so residual fields may not
    # decay to the solver's energy threshold. Cap the run at a fixed duration.
    fdtd = openEMS(NrTS=MAX_TIMESTEPS, EndCriteria=1e-5)
    fdtd.SetGaussExcite(MAX_FREQUENCY_HZ / 2, MAX_FREQUENCY_HZ / 2)
    # Open boundaries absorb fields leaving the model. The bottom boundary is
    # a perfect electric conductor, representing an infinite ground plane.
    fdtd.SetBoundaryCond(["PML_8", "PML_8", "PML_8", "PML_8", "PEC", "PML_8"])

    csx = ContinuousStructure()
    fdtd.SetCSX(csx)
    mesh = csx.GetGrid()
    mesh.SetDeltaUnit(1e-6)

    half_length = LINE_LENGTH_UM / 2
    substrate_top = SUBSTRATE_HEIGHT_UM
    air_top = substrate_top + 3_000
    half_width = args.trace_width_um / 2

    # Mesh lines are made denser around the trace edges, where the electric
    # field changes quickly. A finer mesh takes longer but can improve detail.
    mesh.AddLine("x", [-half_length, -half_length + 800, 0,
                       half_length - 800, half_length])
    mesh.SmoothMeshLines("x", MAX_MESH_CELL_UM, ratio=1.4)
    edge_refine = 50
    mesh.AddLine("y", [-10_000, -half_width - edge_refine,
                       -half_width, -half_width + edge_refine,
                       half_width - edge_refine, half_width,
                       half_width + edge_refine, 10_000])
    mesh.SmoothMeshLines("y", MAX_MESH_CELL_UM, ratio=1.4)
    mesh.AddLine("z", np.r_[np.linspace(0, substrate_top, 9),
                            np.linspace(substrate_top, air_top, 13)])
    mesh.SmoothMeshLines("z", MAX_MESH_CELL_UM, ratio=1.4)

    # FR-4 is represented as a dielectric block. The value 4.2 is an
    # assumption; a real board model should use the fabricator's stackup data.
    dielectric = csx.AddMaterial("assumed_FR4", epsilon=SUBSTRATE_ER)
    dielectric.AddBox([-half_length, -10_000, 0],
                      [half_length, 10_000, substrate_top])

    # Two ports launch and receive the signal. The port helper creates the
    # metal trace. Port 1 is driven; port 2 is passive and measures transmission.
    copper = csx.AddMetal("ideal_copper")
    left = fdtd.AddMSLPort(
        1, copper,
        [-half_length, -half_width, substrate_top],
        [0, half_width, 0], "x", "z",
        excite=1, FeedShift=600, MeasPlaneShift=LINE_LENGTH_UM / 3,
        priority=10)
    right = fdtd.AddMSLPort(
        2, copper,
        [half_length, -half_width, substrate_top],
        [0, half_width, 0], "x", "z",
        excite=0, MeasPlaneShift=LINE_LENGTH_UM / 3,
        priority=10)

    # Save the field geometry separately from the generated field data.
    csx.Write2XML(str(MODEL_DIR / f"{args.case}.xml"))
    print(f"Running openEMS: {LINE_LENGTH_UM/1000:g} mm line, "
          f"{args.trace_width_um/1000:g} mm trace, "
          f"{SUBSTRATE_HEIGHT_UM/1000:g} mm substrate")
    fdtd.Run(str(run_dir), cleanup=True)

    frequencies = np.linspace(10e6, MAX_FREQUENCY_HZ, 401)
    left.CalcPort(str(run_dir), frequencies, ref_impedance=50)
    right.CalcPort(str(run_dir), frequencies, ref_impedance=50)
    s11 = left.uf_ref / left.uf_inc
    s21 = right.uf_ref / left.uf_inc
    s11_db = 20 * np.log10(np.maximum(np.abs(s11), 1e-12))
    s21_db = 20 * np.log10(np.maximum(np.abs(s21), 1e-12))

    csv_path = case_dir / "sparams.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frequency_hz", "S11_dB", "S21_dB"])
        writer.writerows(zip(frequencies, s11_db, s21_db))

    fig, axis = plt.subplots(figsize=(8.2, 4.8), layout="constrained")
    axis.plot(frequencies / 1e9, s11_db, label="S11: reflected")
    axis.plot(frequencies / 1e9, s21_db, label="S21: transmitted")
    axis.set(xlabel="Frequency (GHz)", ylabel="Magnitude (dB)",
             title=f"20 mm, {args.trace_width_um/1000:g} mm wide microstrip over an ideal ground plane")
    axis.grid(True, alpha=0.35)
    axis.set_ylim(-60, max(3, float(np.max(s21_db)) + 1))
    axis.legend()
    plot_path = case_dir / "sparams.png"
    fig.savefig(plot_path, dpi=160)
    plt.close(fig)

    print(f"Saved {csv_path.relative_to(ROOT)}")
    print(f"Saved {plot_path.relative_to(ROOT)}")
    print("Read S11 as the reflected fraction and S21 as the transmitted "
          "fraction. This first model ignores copper and dielectric losses.")


if __name__ == "__main__":
    main()
