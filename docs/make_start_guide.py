#!/usr/bin/env python3
"""Create the one-page PDF guide for the introductory openEMS example."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parent
output = ROOT / "START_HERE.pdf"
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=9, leading=12))
doc = SimpleDocTemplate(str(output), pagesize=letter,
                        rightMargin=0.65*inch, leftMargin=0.65*inch,
                        topMargin=0.55*inch, bottomMargin=0.55*inch)
story = [
    Paragraph("Your first PCB field simulation", styles["Title"]),
    Paragraph("A single microstrip trace in openEMS", styles["Heading2"]),
    Paragraph("This model is deliberately small: one copper trace, one FR-4-like "
              "dielectric block, one ground plane, and two ports. The solver "
              "calculates how an electromagnetic wave reflects from and passes "
              "through the trace.", styles["BodyText"]),
    Spacer(1, 8),
]

diagram = Table([
    ["Port 1  →", "20 mm copper trace", "→  Port 2"],
    ["", "assumed FR-4, εr = 4.2", ""],
    ["", "ideal ground plane", ""],
], colWidths=[1.45*inch, 3.5*inch, 1.45*inch], rowHeights=[0.32*inch]*3)
diagram.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
    ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#fef3c7")),
    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#d1d5db")),
    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#374151")),
    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story += [diagram, Spacer(1, 10),
          Paragraph("Run it", styles["Heading2"]),
          Paragraph("From the simulations directory, run:<br/><font name='Courier'>"
                    "./scripts/run.sh</font>", styles["BodyText"]),
          Spacer(1, 6),
          Paragraph("Read the plot", styles["Heading2"]),
          Paragraph("<b>S11</b> is the part of the signal reflected toward the source. "
                    "Lower S11 means a better match to the 50 Ω port reference. "
                    "<b>S21</b> is the part that reaches the other end. For this "
                    "short, lossless line, S21 should stay near 0 dB.", styles["BodyText"]),
          Spacer(1, 6),
          Paragraph("Change one input at a time", styles["Heading2"]),
          Paragraph("In <font name='Courier'>scripts/run_microstrip.py</font>, change "
                    "<font name='Courier'>TRACE_WIDTH_UM</font> (3000 µm), "
                    "<font name='Courier'>SUBSTRATE_HEIGHT_UM</font> (1600 µm), "
                    "or <font name='Courier'>SUBSTRATE_ER</font> (4.2). Run again "
                    "and compare the new plot with the old one. The first change "
                    "to try is trace width: wider trace usually lowers impedance "
                    "and changes reflection.", styles["BodyText"]),
          Spacer(1, 6),
          Paragraph("Assumptions", styles["Heading2"]),
          Paragraph("The model uses ideal copper and a lossless dielectric. "
                    "It is a learning example, not a prediction of the complete "
                    "SRA board. Use the PCB fabricator's actual stackup values "
                    "before treating a result as a design decision.", styles["Small"])]

doc.build(story)
print(output)
