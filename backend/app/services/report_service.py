"""
PetroNexus Report Generation Service
Produces auditable Engineering Context Packs, Pre-Interval Operational Briefs,
and Offset Intelligence Reports in both structured JSON and printable PDF formats.
"""
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from backend.app.config import settings

class ReportService:

    @staticmethod
    def generate_pdf_context_pack(context_pack_data: Dict[str, Any], output_path: Path) -> str:
        """
        Builds a styled PDF Context Pack using ReportLab.
        """
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a")
        )
        subtitle_style = ParagraphStyle(
            "SubTitleStyle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#0284c7")
        )
        heading2_style = ParagraphStyle(
            "Heading2Style",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "BodyStyle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155")
        )
        alert_style = ParagraphStyle(
            "AlertStyle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#dc2626")
        )

        elements = []

        # Header Title
        elements.append(Paragraph("PETRONEXUS — ACTIVE WELL CONTEXT PACK", title_style))
        elements.append(Paragraph(
            f"Oil India Limited (OIL) • eRTMAC Integrated Operations • Generated: {context_pack_data.get('generated_at')}",
            subtitle_style
        ))
        elements.append(Spacer(1, 12))

        # Active Well Summary Table
        elements.append(Paragraph("1. Active Well Profile", heading2_style))
        act = context_pack_data.get("active_well_summary", {})
        well_table_data = [
            ["Well Name:", act.get("well_name", "N/A"), "Operator:", act.get("operator", "Oil India Limited")],
            ["Current Depth (MD):", f"{act.get('current_depth_m', 'N/A')} m", "Current Formation:", act.get("current_formation", "N/A")],
            ["Target Depth:", f"{act.get('target_depth_m', 'N/A')} m", "Coordinates:", f"{act.get('latitude', '')}, {act.get('longitude', '')}"],
            ["Data Readiness Score:", f"{act.get('readiness_percentage', 82.0)}%", "Operational Status:", act.get("status", "DRILLING_ACTIVE")]
        ]
        t = Table(well_table_data, colWidths=[130, 140, 110, 160])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#1e293b")),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))

        # Look-Ahead Hazards Table
        elements.append(Paragraph("2. Look-Ahead Corridor Hazards (Next 150 m Ahead of Bit)", heading2_style))
        hazards = context_pack_data.get("lookahead_hazards", [])
        if hazards:
            hazard_data = [["Offset Well", "Hazard Type", "Depth (MD)", "Delta Ahead", "Document Citation"]]
            for h in hazards[:5]:
                hazard_data.append([
                    h.get("offset_well_name", ""),
                    h.get("event_type", ""),
                    f"{h.get('hazard_depth_md_m', '')} m",
                    f"+{h.get('delta_ahead_m', '')} m",
                    h.get("source_citation", "")
                ])
            ht = Table(hazard_data, colWidths=[100, 120, 80, 80, 160])
            ht.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
            ]))
            elements.append(ht)
        else:
            elements.append(Paragraph("No critical hazards detected in current lookahead corridor.", body_style))
        elements.append(Spacer(1, 10))

        # Historical Mitigations
        elements.append(Paragraph("3. Documented Offset Mitigations (Playbook)", heading2_style))
        mitigations = context_pack_data.get("historical_mitigations", [])
        for m in mitigations[:3]:
            elements.append(Paragraph(
                f"<b>• {m.get('title')} ({m.get('action_category')})</b>: {m.get('procedure')} [Sources: {', '.join(m.get('evidence_sources', []))}]",
                body_style
            ))
        elements.append(Spacer(1, 10))

        # Memory Gaps
        elements.append(Paragraph("4. PetroNexus Memory Gaps & Missing Data", heading2_style))
        gaps = context_pack_data.get("memory_gaps", [])
        for g in gaps:
            elements.append(Paragraph(
                f"<b>[!] {g.get('title')}</b>: {g.get('description')} Recommendation: {g.get('recommendation')}",
                body_style
            ))
        elements.append(Spacer(1, 10))

        # Operational Disclaimer
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            "<b>OPERATIONAL NOTICE:</b> PetroNexus provides historical and analytical decision support derived from offset-well knowledge bases. Final operational decisions remain with qualified drilling personnel.",
            alert_style
        ))

        doc.build(elements)
        return str(output_path.name)
