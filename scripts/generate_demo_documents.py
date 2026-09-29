"""
PetroNexus Sample Document Generator
Generates realistic PDF, CSV, and LAS files for:
1. WCR-OIL-DEMO-018.pdf (with page 37 describing 2860m Mud Loss & LCM mitigation)
2. DDR-OIL-DEMO-021.pdf (with page 22 describing 2842m Torque Spike & Wiper trip)
3. Mud_Report_OIL-DEMO-011.pdf (with page 15 describing seepage losses)
4. Current_Well_Report_OIL-DEMO-023.pdf (Daily drilling report at 2846m MD)
5. Current_Well_Telemetry_OIL-DEMO-023.csv
6. Current_Well_Survey_OIL-DEMO-023.csv
7. Current_Well_Log_OIL-DEMO-023.las
"""
from pathlib import Path
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DOC_DIR = Path(__file__).resolve().parent.parent / "documents"
DOC_DIR.mkdir(parents=True, exist_ok=True)

def generate_pdf_wcr_018():
    path = DOC_DIR / "WCR-OIL-DEMO-018.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"))
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, leading=16, textColor=colors.HexColor("#0284c7"))
    body = ParagraphStyle("B", parent=styles["Normal"], fontSize=9, leading=13, textColor=colors.HexColor("#334155"))

    story = []

    # Pages 1 to 36 (Summary intro)
    for p in range(1, 37):
        story.append(Paragraph(f"OIL INDIA LIMITED — WELL COMPLETION REPORT: OIL-DEMO-018 (Page {p})", title_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Field: Duliajan Basin • Spud: 2025-01-10 • TD: 3150 m • Status: Completed Development Well", body))
        story.append(Spacer(1, 15))
        story.append(Paragraph("1.0 Well Summary & Geological Succession", h2_style))
        story.append(Paragraph("This report compiles operational, petrophysical, and casing evaluation records for well OIL-DEMO-018.", body))
        story.append(Spacer(1, 20))
        table_data = [
            ["Formation", "Top MD (m)", "Bottom MD (m)", "Lithology"],
            ["Alluvium", "0.0", "450.0", "Gravel & Sand"],
            ["Dhekiajuli", "450.0", "1050.0", "Sandstone"],
            ["Girujan Clay", "1050.0", "1700.0", "Claystone"],
            ["Tipam Sandstone", "1700.0", "2400.0", "Massive Sandstone"],
            ["Formation-X", "2810.0", "3050.0", "Interbedded Sand & Shale"]
        ]
        t = Table(table_data, colWidths=[130, 80, 80, 160])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(PageBreak())

    # PAGE 37: THE FAMOUS MUD LOSS AT 2860M!
    story.append(Paragraph("OIL INDIA LIMITED — WELL COMPLETION REPORT: OIL-DEMO-018 (Page 37)", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("SECTION 6.4: CRITICAL DRILLING EVENT LOG — FORMATION-X INTERVAL", h2_style))
    story.append(Paragraph(
        "<b>DATE & TIME:</b> 2025-04-12 14:30 hrs • <b>MEASURED DEPTH:</b> 2860.0 m MD (2818.5 m TVD)<br/>"
        "<b>FORMATION:</b> Formation-X (Upper Arenaceous Member)<br/>"
        "<b>EVENT TYPE:</b> Severe Lost Circulation / Partial Mud Loss (45 bbl/hr)",
        body
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Detailed Narrative & Root Cause Analysis:</b>", h2_style))
    story.append(Paragraph(
        "While drilling 8-1/2 in hole at 2860.0 m MD with 1.22 SG polymer WBM, penetration rate accelerated from "
        "12.0 m/hr to 24.5 m/hr (drilling break). Immediately upon drilling 0.8 m into the sandstone streak, active pit "
        "volume began dropping at 45 bbl/hr. Total fluid lost prior to treatment was 95 bbl.<br/><br/>"
        "<b>Root Cause:</b> Penetration into sub-seismic open micro-fracture network with depleted reservoir pressure "
        "exhibiting an equivalent pore pressure of 1.08 SG.",
        body
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Implemented Historical Mitigation:</b>", h2_style))
    story.append(Paragraph(
        "1. Immediately picked up bit off bottom to 2845 m MD and shut down mud pumps.<br/>"
        "2. Mixed and spotted a 30 bbl LCM pill comprising 25 ppb medium walnut shells + 15 ppb coarse calcium carbonate.<br/>"
        "3. Allowed pill to soak across 2860 m interval for 90 minutes under static conditions.<br/>"
        "4. Resumed circulation at throttled flow rate of 1950 LPM (reduced from 2250 LPM) with ECD maintained below 1.28 SG.<br/>"
        "5. Full fluid returns established with zero further losses across interval.",
        body
    ))
    story.append(Spacer(1, 15))
    story.append(PageBreak())

    # Page 38 (Conclusion)
    story.append(Paragraph("OIL INDIA LIMITED — WELL COMPLETION REPORT: OIL-DEMO-018 (Page 38)", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("SECTION 6.5: CEMENTING & CASING INTEGRITY RECORD", h2_style))
    story.append(Paragraph("Successfully set 7 in Production Liner at 3145 m MD with Class G cement.", body))

    doc.build(story)
    print("Generated WCR-OIL-DEMO-018.pdf (38 pages).")

def generate_pdf_ddr_021():
    path = DOC_DIR / "DDR-OIL-DEMO-021.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"))
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, leading=16, textColor=colors.HexColor("#0284c7"))
    body = ParagraphStyle("B", parent=styles["Normal"], fontSize=9, leading=13, textColor=colors.HexColor("#334155"))

    story = []
    # Pages 1 to 21
    for p in range(1, 22):
        story.append(Paragraph(f"OIL INDIA LIMITED — DAILY DRILLING REPORT: OIL-DEMO-021 (Day {p}, Page {p})", title_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Field: Duliajan Basin • Operation: Drilling 8-1/2 in Directional Hole • Rig: OIL Rig #4", body))
        story.append(PageBreak())

    # PAGE 22: THE TORQUE SPIKE AT 2842M!
    story.append(Paragraph("OIL INDIA LIMITED — DAILY DRILLING REPORT: OIL-DEMO-021 (Day 22, Page 22)", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("OPERATIONAL INCIDENT: TORQUE SPIKE & TIGHT HOLE AT 2842.0 M MD", h2_style))
    story.append(Paragraph(
        "<b>DATE:</b> 2025-08-19 • <b>DEPTH:</b> 2842.0 m MD (2802.0 m TVD) • <b>INCLINATION:</b> 31.8 deg<br/>"
        "<b>FORMATION:</b> Formation-X (Upper Siltstone/Shale Transition)",
        body
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "<b>Description of Event:</b> While drilling at 2842 m MD, rotary torque surged violently from 16.5 kN.m baseline "
        "to over 23.2 kN.m. Top drive stalled twice. On picking up string, observed 32 tons overpull. "
        "Shaker screen showed excessive volume of splintery cavings indicating wellbore instability.",
        body
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Action Taken / Mitigation:</b>", h2_style))
    story.append(Paragraph(
        "1. Picked up string into 9-5/8 in casing shoe at 2150 m MD.<br/>"
        "2. Pumped 25 bbl high-viscosity pill with 45 sec funnel viscosity.<br/>"
        "3. Reamed tight spot between 2820 m and 2842 m MD with 80 RPM and controlled flow.<br/>"
        "4. Mud weight raised from 1.21 SG to 1.24 SG to stabilize brittle shale cavings.",
        body
    ))
    doc.build(story)
    print("Generated DDR-OIL-DEMO-021.pdf (22 pages).")

def generate_pdf_current_well_023():
    path = DOC_DIR / "Current_Well_Report_OIL-DEMO-023.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"))
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, leading=16, textColor=colors.HexColor("#0284c7"))
    body = ParagraphStyle("B", parent=styles["Normal"], fontSize=9, leading=13, textColor=colors.HexColor("#334155"))

    story = []
    story.append(Paragraph("OIL INDIA LIMITED — DAILY DRILLING REPORT (ACTIVE WELL)", title_style))
    story.append(Paragraph("eRTMAC Central Operations Console • Current Well Report", h2_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>1.0 WELL IDENTITY & LOCATION</b>", h2_style))
    story.append(Paragraph(
        "Well Name: OIL-DEMO-023<br/>"
        "Well ID: OIL-AS-023<br/>"
        "Field: Duliajan Basin<br/>"
        "Operator: Oil India Limited (OIL)<br/>"
        "Latitude: 27.352000<br/>"
        "Longitude: 95.318000<br/>"
        "Current Status: DRILLING_ACTIVE",
        body
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>2.0 CURRENT DEPTH & FORMATION CONTEXT</b>", h2_style))
    story.append(Paragraph(
        "Current Measured Depth (MD): 2846.0 m<br/>"
        "True Vertical Depth (TVD): 2805.2 m<br/>"
        "Target Depth (TD): 3200.0 m<br/>"
        "Current Formation: Formation-X<br/>"
        "Formation Top: 2812.0 m<br/>"
        "Lithology: Interbedded Sandstone and Brittle Shale",
        body
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>3.0 REAL-TIME DRILLING TELEMETRY SNAPSHOT</b>", h2_style))
    param_table = [
        ["Parameter", "Observed Value", "Engineering Units"],
        ["Rate of Penetration (ROP)", "14.5", "m/hr"],
        ["Weight on Bit (WOB)", "12.0", "metric tons"],
        ["Rotary Speed (RPM)", "110.0", "RPM"],
        ["Drilling Torque", "16.8", "kN.m"],
        ["Equivalent Circulating Density (ECD)", "1.28", "SG"],
        ["Static Mud Weight", "1.22", "SG"],
        ["Standpipe Pressure (SPP)", "2450.0", "psi"],
        ["Flow Rate", "2150.0", "LPM"],
        ["Hook Load", "85.0", "metric tons"]
    ]
    t = Table(param_table, colWidths=[200, 120, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>4.0 WELL ENGINEERING & DRILL STRING</b>", h2_style))
    story.append(Paragraph(
        "BHA Assembly: 8-1/2 in PDC 5-Blade Matrix Body + Rotary Steerable System (RSS) + MWD/LWD + Stabilizer.<br/>"
        "Casing: 9-5/8 in 40# L-80 Intermediate Casing Shoe set at 2150.0 m MD.<br/>"
        "Mud Program: Water-Based Polymer Mud (WBM).",
        body
    ))

    doc.build(story)
    print("Generated Current_Well_Report_OIL-DEMO-023.pdf.")

def generate_csv_and_las():
    # 1. Telemetry CSV
    rows = []
    for d in range(2750, 2847):
        depth = float(d)
        rows.append({
            "depth_md_m": depth,
            "rop_m_hr": round(14.0 + (d % 5) * 0.4, 2),
            "wob_ton": round(11.5 + (d % 3) * 0.3, 2),
            "rpm": 110.0,
            "torque_kn_m": round(16.2 + (d % 4) * 0.3, 2),
            "ecd_sg": 1.28,
            "mud_weight_sg": 1.22,
            "spp_psi": 2450.0,
            "flow_rate_lpm": 2150.0
        })
    df = pd.DataFrame(rows)
    df.to_csv(DOC_DIR / "Current_Well_Telemetry_OIL-DEMO-023.csv", index=False)

    # 2. Directional Survey CSV
    survey_rows = [
        {"md": 0.0, "inc": 0.0, "azi": 0.0},
        {"md": 500.0, "inc": 1.2, "azi": 45.0},
        {"md": 1000.0, "inc": 8.5, "azi": 52.0},
        {"md": 1500.0, "inc": 18.2, "azi": 54.0},
        {"md": 2000.0, "inc": 26.5, "azi": 55.0},
        {"md": 2500.0, "inc": 31.0, "azi": 56.5},
        {"md": 2846.0, "inc": 32.4, "azi": 57.0}
    ]
    pd.DataFrame(survey_rows).to_csv(DOC_DIR / "Current_Well_Survey_OIL-DEMO-023.csv", index=False)

    # 3. Sample LAS file
    las_content = """~VERSION INFORMATION
 VERS.                          2.0 :   CWLS LOG ASCII STANDARD -VERSION 2.0
 WRAP.                           NO :   ONE LINE PER DEPTH STEP
~WELL INFORMATION
#MNEM.UNIT       DATA                       DESCRIPTION
#---------       ----                       -----------
 STRT.M          2750.0000                  : START DEPTH
 STOP.M          2846.0000                  : STOP DEPTH
 STEP.M          0.5000                     : STEP
 NULL.           -999.25                    : NULL VALUE
 COMP.           OIL INDIA LIMITED          : COMPANY
 WELL.           OIL-DEMO-023               : WELL
 FLD .           DULIAJAN                   : FIELD
 DATE.           2026-09-29                 : LOG DATE
~CURVE INFORMATION
#MNEM.UNIT       API CODES                  CURVE DESCRIPTION
#---------       ---------                  -----------------
 DEPT.M                                     : 1  DEPTH
 GR  .GAPI                                  : 2  GAMMA RAY
 RES .OHMM                                  : 3  DEEP RESISTIVITY
 RHOB.G/C3                                  : 4  BULK DENSITY
~A  DEPT     GR       RES      RHOB
 2840.0   62.5     14.2     2.34
 2842.0   68.1     12.8     2.36
 2844.0   55.4     18.5     2.29
 2846.0   51.2     22.4     2.26
"""
    with open(DOC_DIR / "Current_Well_Log_OIL-DEMO-023.las", "w") as f:
        f.write(las_content)

    print("Generated CSV and LAS demo files.")

if __name__ == "__main__":
    generate_pdf_wcr_018()
    generate_pdf_ddr_021()
    generate_pdf_current_well_023()
    generate_csv_and_las()
