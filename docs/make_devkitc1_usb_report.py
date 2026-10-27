#!/usr/bin/env python3
"""Generate the PDF guide for the DevKitC-1 native USB openEMS example."""

from pathlib import Path
import re

import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak


DOCS = Path(__file__).resolve().parent
ROOT = DOCS.parent
RESULTS = ROOT / "results" / "devkitc1_usb"
OUTPUT = DOCS / "DevKitC1_USB_Simulation.pdf"

SCHEMATIC = "https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf"
GUIDE = "https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html"
ESD_DATASHEET = "https://datasheet.lcsc.com/lcsc/2211081800_Leiditech-LESD5D5-0CT1G_C5246195.pdf"


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleX", parent=styles["Title"], fontSize=20,
                          leading=24, textColor=colors.HexColor("#172033"), spaceAfter=12))
styles.add(ParagraphStyle(name="HeadX", parent=styles["Heading2"], fontSize=11,
                          leading=14, textColor=colors.HexColor("#1d4ed8"), spaceBefore=10))
styles.add(ParagraphStyle(name="BodyX", parent=styles["BodyText"], fontSize=9,
                          leading=12, spaceAfter=6))
styles.add(ParagraphStyle(name="SmallX", parent=styles["BodyText"], fontSize=7.5,
                          leading=10, spaceAfter=4))


def p(value, style="BodyX"):
    return Paragraph(value, styles[style])


def scaled_image(path, width_mm):
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        width_px, height_px = im.size
    width = width_mm*mm
    return Image(str(path), width=width, height=width*height_px/width_px)


def near(data, frequency_hz):
    return data[np.argmin(abs(data["frequency_hz"]-frequency_hz))]


def run_status(case):
    log = (RESULTS / case / "run.log").read_text()
    match = re.search(r"RunFDTD: end-criteria.*?reached after (\d+) timesteps \(([^)]+)\)", log)
    if match:
        return f"Field decay target reached after {int(match.group(1)):,} steps ({match.group(2)})."
    return "Field decay target was not confirmed; inspect the run log."


def build():
    bare = np.genfromtxt(RESULTS / "bare" / "sparams.csv", delimiter=",", names=True)
    loaded = np.genfromtxt(RESULTS / "esd15pf" / "sparams.csv", delimiter=",", names=True)
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=18*mm,
                            rightMargin=18*mm, topMargin=17*mm, bottomMargin=17*mm,
                            title="ESP32-S3-DevKitC-1 native USB openEMS model")
    story = [p("ESP32-S3-DevKitC-1 native USB path", "TitleX"),
             p("An openEMS model of one passive PCB interconnect section. It is not a simulation of the ESP32-S3 chip or the complete development board."),
             p("What comes from the board", "HeadX"),
             p("Espressif's v1.1 schematic connects connector J4 D- to GPIO19 and D+ to GPIO20. Protection diodes D8 and D9 connect those signals to ground. The indicated part is LESD5D5.0CT1G; its datasheet lists 15 pF typical junction capacitance at 0 V and 1 MHz. The loaded run replaces each diode with a fixed 15 pF shunt capacitor. This is a linear small-signal approximation, not ESD clamping behavior."),
             p("What the geometry assumes", "HeadX")]
    table = Table([
        ["Quantity", "Model value", "Status"],
        ["Straight pair length", "10 mm", "Assumed"],
        ["Each trace width / gap", "0.25 mm / 0.20 mm", "Assumed"],
        ["Dielectric to ground", "0.20 mm, er = 4.2", "Assumed"],
        ["Copper / dielectric loss", "Ideal copper, lossless FR-4", "Simplification"],
        ["Port reference", "50 ohm per line (100 ohm diff)", "Chosen for simulation"],
        ["ESD capacitance", "0 or 15 pF per line", "15 pF from part datasheet"],
    ], colWidths=[48*mm, 65*mm, 61*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172033")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [table, Spacer(1, 6*mm),
              scaled_image(RESULTS / "esd15pf" / "geometry.png", 174),
              p("The published PCB layout was not imported. Pad shapes and all route dimensions above are illustrative. Use the XML in AppCSXCAD to rotate and inspect the 3D model.", "SmallX"),
              PageBreak(),
              p("Two electrical runs", "TitleX"),
              p("Both runs use the same ideal trace geometry and opposite-polarity drives on D+ and D-. One run has no diode load; the other has a 15 pF shunt on each signal."),
              scaled_image(RESULTS / "comparison.png", 174),
              p("Reading the result", "HeadX")]
    at10_b, at10_l = near(bare, 10e6), near(loaded, 10e6)
    at1g_b, at1g_l = near(bare, 1e9), near(loaded, 1e9)
    story += [p(f"At 10 MHz, Sdd21 is {at10_b['Sdd21_dB']:.3f} dB unloaded and "
                f"{at10_l['Sdd21_dB']:.3f} dB with the capacitance proxy. "
                f"Near 1 GHz, it is {at1g_b['Sdd21_dB']:.3f} dB unloaded and "
                f"{at1g_l['Sdd21_dB']:.3f} dB loaded. The fixed shunt capacitance increasingly loads fast spectral components. These frequency-domain curves alone do not establish a USB eye diagram or USB compliance."),
              p("Solver status", "HeadX"),
              p("Unloaded: " + run_status("bare")),
              p("15 pF proxy: " + run_status("esd15pf")),
              p("A reached field-decay target does not prove mesh convergence. These first-mesh numbers are exploratory. Exact board prediction requires the routed copper, stackup, diode package/parasitics, connector, chip input model, and convergence checks."),
              p("Run and inspect", "HeadX"),
              p("From simulations/: <font name='Courier'>./scripts/run_devkitc1_usb.sh</font>; "
                "<font name='Courier'>./scripts/run_devkitc1_usb.sh --case devkitc1_usb_esd15pf --esd-cap-pf 15</font>; "
                "<font name='Courier'>./scripts/view_devkitc1_usb.sh</font>.", "SmallX"),
              p("Sources", "HeadX"),
              p(f"<link href='{GUIDE}'>Espressif DevKitC-1 v1.1 guide</link> | "
                f"<link href='{SCHEMATIC}'>Espressif schematic</link> | "
                f"<link href='{ESD_DATASHEET}'>Leiditech component datasheet</link>", "SmallX")]
    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build()
