#!/usr/bin/env python3
"""Create a beginner-friendly experiment plan for the openEMS microstrip model."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "Microstrip_Experiment_Plan.pdf"

INK = colors.HexColor("#172033")
BLUE = colors.HexColor("#1D4ED8")
PALE_BLUE = colors.HexColor("#EAF2FF")
PALE_GOLD = colors.HexColor("#FFF6DB")
PALE_GREEN = colors.HexColor("#EAF7EF")
GRID = colors.HexColor("#D5DCE8")
MUTED = colors.HexColor("#536174")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=25, leading=30, textColor=INK, alignment=TA_CENTER,
    spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CoverSub", parent=styles["Normal"], fontSize=12, leading=17,
    textColor=MUTED, alignment=TA_CENTER, spaceAfter=14,
))
styles.add(ParagraphStyle(
    name="H1x", parent=styles["Heading1"], fontSize=17, leading=21,
    textColor=INK, spaceBefore=5, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="H2x", parent=styles["Heading2"], fontSize=12, leading=15,
    textColor=BLUE, spaceBefore=7, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="Bodyx", parent=styles["BodyText"], fontSize=9.5, leading=13.5,
    textColor=INK, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Smallx", parent=styles["BodyText"], fontSize=8, leading=10.5,
    textColor=MUTED, spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="Cellx", parent=styles["BodyText"], fontSize=8, leading=10.3,
    textColor=INK, spaceAfter=0,
))
styles.add(ParagraphStyle(
    name="CellHeadx", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=8, leading=10.3, textColor=colors.white, spaceAfter=0,
))
styles.add(ParagraphStyle(
    name="Calloutx", parent=styles["BodyText"], fontSize=9.3, leading=13,
    textColor=INK, leftIndent=7, rightIndent=7, spaceBefore=5, spaceAfter=5,
))


def p(text, style="Bodyx"):
    return Paragraph(text, styles[style])


def bullet(text):
    return p("•&nbsp;&nbsp;" + text)


def callout(text, bg=PALE_BLUE):
    box = Table([[p(text, "Calloutx")]], colWidths=[174 * mm])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.6, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return box


def data_table(headers, rows, widths, row_bgs=None):
    data = [[p(x, "CellHeadx") for x in headers]]
    for row in rows:
        data.append([p(x, "Cellx") for x in row])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        bg = row_bgs[i - 1] if row_bgs else (colors.white if i % 2 else colors.HexColor("#F6F8FB"))
        commands.append(("BACKGROUND", (0, i), (-1, i), bg))
    table.setStyle(TableStyle(commands))
    return table


def footer(canvas, doc):
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 9 * mm, "openEMS microstrip learning plan")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"{doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
    topMargin=17 * mm, bottomMargin=20 * mm,
    title="Microstrip Model: Experiment Plan",
    author="",
    subject="A staged plan for learning and validating the existing openEMS microstrip model",
)

story = []

# Page 1: orientation and reading the plot.
story += [Spacer(1, 15 * mm),
          p("Microstrip Model", "CoverTitle"),
          p("A gentle experiment plan before simulating the SRA PCB", "CoverSub"),
          callout("<b>The idea:</b> keep the model simple, change one thing at a time, and learn what the S-parameter plot does when the geometry or material changes.", PALE_GREEN),
          Spacer(1, 7 * mm),
          p("What the current model contains", "H1x"),
          p("The script <font name='Courier'>run_microstrip.py</font> describes one straight trace above a dielectric slab and a ground plane. Port 1 sends in a pulse; port 2 measures what arrives. The model is a practice structure. It does not import the SRA PCB.")]

diagram = Table([
    [p("Port 1<br/><font color='#536174'>send pulse</font>", "Cellx"),
     p("20 mm trace<br/><font color='#536174'>3 mm wide</font>", "Cellx"),
     p("Port 2<br/><font color='#536174'>measure arrival</font>", "Cellx")],
    ["", p("Assumed dielectric: εr = 4.2<br/>Height: 1.6 mm", "Cellx"), ""],
    ["", p("Ideal ground plane", "Cellx"), ""],
], colWidths=[42 * mm, 82 * mm, 42 * mm], rowHeights=[13 * mm, 12 * mm, 10 * mm])
diagram.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), PALE_BLUE),
    ("BACKGROUND", (0, 1), (-1, 1), PALE_GOLD),
    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#E9EDF3")),
    ("BOX", (0, 0), (-1, -1), 0.7, GRID),
    ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.white),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story += [diagram, Spacer(1, 6 * mm),
          p("First: understand dB", "H1x"),
          p("The plot uses dB to express a ratio. Here the ratio is the reflected or transmitted wave compared with the wave sent into the line. A dB value is not a voltage by itself.")]
story.append(data_table(
    ["Plot value", "Wave amplitude ratio", "Power ratio (same reference impedance)"],
    [["0 dB", "1×: same amplitude", "100%"],
     ["−3 dB", "about 0.71×", "about 50%"],
     ["−20 dB", "0.1×: one tenth", "1%"],
     ["−40 dB", "0.01×: one hundredth", "0.01%"]],
    [30 * mm, 58 * mm, 78 * mm]))
story += [Spacer(1, 3 * mm),
          bullet("<b>S11</b> is the reflected wave. A more negative S11 means less reflection."),
          bullet("<b>S21</b> is the wave transmitted to port 2. A value closer to 0 dB means more power is transmitted."),
          callout("The script normalizes the port calculations to 50 Ω. That is a reference for reporting S-parameters; it does not by itself make the physical trace exactly 50 Ω.", PALE_GOLD),
          PageBreak()]

# Page 2: credibility gates.
story += [p("Before changing the design", "H1x"),
          p("First make sure the baseline is trustworthy. Otherwise a difference between plots could come from numerical settings instead of the change you intended.")]
story += [p("Gate 1 — save a baseline", "H2x"),
          bullet("Keep the present inputs: 20 mm length, 3 mm width, 1.6 mm substrate height, εr = 4.2, and 250 µm maximum mesh cell."),
          bullet("Save the script inputs, the run log, and a copy of the S-parameter CSV and plot."),
          bullet("The session notes say the current run reached its time-step cap before the field-decay target. Mark this first plot as <b>exploratory</b>.")]
story += [p("Gate 2 — check the run has settled", "H2x"),
          p("Repeat the baseline with a larger time-step allowance, leaving geometry and mesh unchanged. Compare the S11 and S21 curves. A usable baseline should reach the solver's stopping target, or the curves should be shown to stop changing as the allowed run time increases. Record clearly if the cap is still reached.")]
story += [p("Gate 3 — check mesh sensitivity", "H2x"),
          p("Once the time history is adequate, compare the present 250 µm maximum cell size with a finer mesh such as 125 µm. Keep the same geometry and materials. Compare the whole curves, especially resonances and sharp features. Finer cells increase cost and also constrain the FDTD time step, so refinement should answer a question rather than be done blindly. See the official <link href='https://docs.openems.de/en/latest/concepts/mesh.html' color='#1D4ED8'>openEMS mesh guidance</link>.")]
story += [callout("Do not begin the parameter sweeps until you can distinguish a real curve change from a result that changes because the run stopped too early or the mesh changed.", PALE_GOLD),
          p("How to compare two runs", "H2x"),
          data_table(["Keep fixed", "Change", "Compare"],
                     [["Everything else", "One input only", "S11 and S21 over the same frequency range"],
                      ["Frequency grid and port setup", "Geometry or material value", "Curve shape, key frequencies, and run status"]],
                     [52 * mm, 52 * mm, 62 * mm]),
          Spacer(1, 4 * mm),
          p("For every run, use a descriptive label such as <font name='Courier'>width_2p7mm</font>. Keep the original CSV instead of overwriting it.", "Smallx"),
          PageBreak()]

# Page 3: simple sweeps.
story += [p("Experiments 1–4: the straight line", "H1x"),
          p("These experiments use the existing straight-line model. They need only small changes to the constants near the top of <font name='Courier'>run_microstrip.py</font>.")]
story.append(data_table(
    ["Experiment", "Change one thing", "Look for / learn"],
    [["1. Trace width", "Try 2.4, 3.0, and 3.6 mm. Change <font name='Courier'>TRACE_WIDTH_UM</font>.", "A wider strip generally has lower characteristic impedance. Watch how the reflection changes. The direction and size of the S11 change depend on the port and stackup."],
     ["2. Substrate height", "Try 1.3, 1.6, and 1.9 mm as sensitivity cases.", "The spacing between trace and ground affects impedance and field distribution. These are learning values, not a substitute for the real board stackup."],
     ["3. Relative permittivity", "Try εr = 3.8, 4.2, and 4.6 as sensitivity cases.", "The electric field travels more slowly in a higher-permittivity environment, changing phase and delay. Use verified material data for any board-specific conclusion."],
     ["4. Line length", "Try 10, 20, and 40 mm. Change <font name='Courier'>LINE_LENGTH_UM</font>.", "A longer line accumulates more phase delay. In this ideal lossless model, length alone should not create physical conductor or dielectric loss."],
    ], [31 * mm, 59 * mm, 76 * mm]))
story += [Spacer(1, 5 * mm),
          p("An optional plot upgrade: phase", "H2x"),
          p("The current script plots only the magnitude of S11 and S21 in dB. S21 also has a phase. Plotting phase versus frequency shows how much the wave rotates as it travels along the line. From phase versus frequency, you can estimate group delay. This is a script change, so do it after the basic magnitude sweeps are understood."),
          callout("For this current model, the dielectric is lossless and the metal is ideal. Do not interpret S21 below 0 dB as a measured PCB loss without first validating the run and adding realistic material losses.", PALE_BLUE),
          p("Keep a small run log", "H2x"),
          data_table(["Run name", "Changed input", "Run reached target?", "What changed in S11 / S21?"],
                     [["baseline", "none", "yes / no", "starting reference"],
                      ["width_2p4mm", "trace width", "yes / no", "notes"],
                      ["er_4p6", "relative permittivity", "yes / no", "notes"]],
                     [35 * mm, 36 * mm, 42 * mm, 53 * mm]),
          PageBreak()]

# Page 4: complexity ladder.
story += [p("Experiments 5–8: realistic effects", "H1x"),
          p("Add these only after the straight-line baseline and simple sweeps are behaving consistently. Each new feature adds a new modeling question.")]
story.append(data_table(
    ["Experiment", "Add to the geometry/model", "What it teaches"],
    [["5. Losses", "Finite copper conductivity and dielectric loss tangent.", "S21 falls as energy is dissipated in the conductors and dielectric. Compare against the ideal-material baseline. Use actual frequency-dependent material data if available."],
     ["6. One discontinuity", "Choose a width step, a 90° bend, or a small gap. Add only one.", "A geometric change can reflect energy and create frequency-dependent behavior. Compare the feature against the straight line."],
     ["7. Open stub", "Branch a short open-ended trace from the main line; sweep the stub length.", "A stub can create a dip (notch) in S21 near a resonance. The official openEMS microstrip tutorial demonstrates this experiment."],
     ["8. Nearby trace", "Add a second parallel line and a receiving port. Change spacing or parallel length one at a time.", "Signal can couple from one trace into another. With port 1 active and port 2 passive the existing model gets S11 and S21; a full multiport matrix requires each port to be excited in its own run."],
    ], [28 * mm, 62 * mm, 76 * mm]))
story += [Spacer(1, 5 * mm),
          p("Field pictures", "H2x"),
          p("The script currently writes port results and S-parameters; it does not save a field movie or field map. Later, add a small field-dump region near the trace or discontinuity. A field view can show where energy is concentrated, but it does not replace checking convergence or S-parameters."),
          p("Useful references", "H2x"),
          p("• <link href='https://docs.openems.de/en/latest/concepts/ports.html' color='#1D4ED8'>openEMS ports</link> — port excitation, reference impedance, and S-parameter runs.<br/>"
            "• <link href='https://docs.openems.de/en/latest/concepts/mesh.html' color='#1D4ED8'>openEMS mesh</link> — mesh placement, resolution, and time-step cost.<br/>"
            "• <link href='https://docs.openems.de/en/latest/python/openEMS/Tutorials/MSL_NotchFilter.html' color='#1D4ED8'>openEMS microstrip notch-filter tutorial</link> — straight line with an open-ended stub.")]
story += [callout("Do not add a bend, stub, losses, and a second trace all at once. If the curve changes, you would not know which addition caused it.", PALE_GOLD),
          PageBreak()]

# Page 5: actual PCB transition and worksheet.
story += [p("When to move to the SRA PCB", "H1x"),
          p("The microstrip model has taught you how the solver, ports, mesh, and S-parameter plots behave. The next step is one small real PCB feature, not the whole board at once."),
          p("Before modeling a real feature", "H2x"),
          bullet("Find the fabricator's actual layer stackup, dielectric properties, and copper thickness."),
          bullet("Choose one routed net or local feature with a clear question, such as a short transmission path, bend, via transition, or pair of coupled traces."),
          bullet("Map only the needed copper, dielectric layers, vias, and return path into the model."),
          bullet("Place ports on understandable cross-sections and confirm the reference planes."),
          bullet("Repeat the convergence checks on that feature before treating its result as meaningful."),
          callout("A verified small-feature model gives a useful next milestone. A microstrip tutorial result alone does not predict the behavior of the entire SRA PCB.", PALE_GREEN),
          p("Experiment worksheet", "H2x"),
          data_table(["Question", "Your notes"],
                     [["What do I expect to happen?", ""],
                      ["Which single parameter will I change?", ""],
                      ["Which settings must stay fixed?", ""],
                      ["Did the solver reach its stopping target?", ""],
                      ["What happened to S11?", ""],
                      ["What happened to S21?", ""],
                      ["What will I try next?", ""]],
                     [69 * mm, 97 * mm], row_bgs=[colors.white] * 7),
          Spacer(1, 5 * mm),
          p("Current script and notes", "H2x"),
          p("Script: <font name='Courier'>simulations/scripts/run_microstrip.py</font><br/>"
            "Current-run note: <font name='Courier'>simulations/OPENEMS_SESSION_CONTEXT.md</font><br/>"
            "The script writes geometry to <font name='Courier'>models/microstrip.xml</font> and S-parameter outputs under <font name='Courier'>results/</font>.", "Smallx")]

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUTPUT)
