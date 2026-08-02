"""
MCRDSE Sprint 4 – PDF Report Generator
======================================
Publication-grade PDF generator using ReportLab Platypus framework.

Features:
- 10 complete report sections.
- Colored sanction verdict banners (Green = Approved, Amber = Review/Conditional, Red = Rejected).
- Numbered page footers ("Page X of Y" style).
- Formatted tables with color-coded compliance status badges.
- Embedded verification QR codes.
"""

from __future__ import annotations

import base64
import io
import logging
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.export.schemas import ReportData

logger = logging.getLogger("app.export.pdf_generator")


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to calculate total page count and draw header/footer.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Do not draw header on cover page (page 1)
        if self._pageNumber > 1:
            # Header
            self.drawString(54, 800, "MUNICIPAL COMPLIANCE REPORTING & DECISION SUPPORT SYSTEM")
            self.drawRightString(541, 800, "CONFIDENTIAL — OFFICIAL USE ONLY")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 792, 541, 792)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 541, 45)

        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(541, 32, footer_text)
        self.drawString(54, 32, "BBMP Urban Development & Plan Sanctioning Authority © 2026")
        self.restoreState()


class PDFReportGenerator:
    """
    ReportLab PDF generator for municipal compliance reports.
    """

    @staticmethod
    def generate_pdf(report_data: ReportData) -> bytes:
        """
        Generate PDF report bytes from canonical ReportData.
        """
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
            spaceAfter=8,
        )

        subtitle_style = ParagraphStyle(
            "CoverSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#475569"),
            spaceAfter=20,
        )

        h1_style = ParagraphStyle(
            "SecHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=14,
            spaceAfter=8,
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
        )

        table_body_style = ParagraphStyle(
            "TableBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1e293b"),
        )

        story = []

        ctx = report_data.decision_context
        bld = ctx.evidence_bundle.building
        gis = ctx.evidence_bundle.gis
        cmp = ctx.evidence_bundle.compliance
        cls = ctx.evidence_bundle.classification
        app = ctx.approval
        risk = ctx.risk
        recs = ctx.recommendations
        summary = ctx.summary

        # ── 1. Cover Page ─────────────────────────────────────────────────────
        story.append(Spacer(1, 20))
        story.append(Paragraph("MUNICIPAL PLAN SANCTION AUDIT REPORT", title_style))
        story.append(Paragraph(f"BBMP Building Plan Sanctioning & Compliance Engine | Report ID: {report_data.report_id}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563eb"), spaceAfter=15))

        # Sanction verdict banner
        banner_bg = "#dcfce7" if app.status_category == "APPROVED" else ("#fee2e2" if app.status_category == "REJECTED" else "#fef3c7")
        banner_fg = "#166534" if app.status_category == "APPROVED" else ("#991b1b" if app.status_category == "REJECTED" else "#92400e")

        banner_text = f"<b>STATUS VERDICT: {app.status_category}</b><br/>{app.sanction_verdict}"
        banner_p = Paragraph(f"<font color='{banner_fg}'>{banner_text}</font>", body_style)

        banner_table = Table([[banner_p]], colWidths=[487])
        banner_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(banner_bg)),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(banner_fg)),
            ("PADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(banner_table)
        story.append(Spacer(1, 15))

        # Key Metadata Summary Table
        meta_data = [
            [Paragraph("<b>Building Name:</b>", table_body_style), Paragraph(bld.building_name, table_body_style),
             Paragraph("<b>Readiness Score:</b>", table_body_style), Paragraph(f"<b>{app.readiness_score:.1f} / 100</b>", table_body_style)],
            [Paragraph("<b>IFC File:</b>", table_body_style), Paragraph(bld.ifc_file, table_body_style),
             Paragraph("<b>Overall Risk:</b>", table_body_style), Paragraph(f"<b>{risk.overall_risk_level}</b>", table_body_style)],
            [Paragraph("<b>Ward / Zone:</b>", table_body_style), Paragraph(f"{gis.ward} ({gis.zone})", table_body_style),
             Paragraph("<b>Authority:</b>", table_body_style), Paragraph(gis.authority, table_body_style)],
            [Paragraph("<b>Generated At:</b>", table_body_style), Paragraph(report_data.generated_at.strftime("%Y-%m-%d %H:%M UTC"), table_body_style),
             Paragraph("<b>Software Version:</b>", table_body_style), Paragraph(ctx.evidence_bundle.software_version, table_body_style)],
        ]
        t_meta = Table(meta_data, colWidths=[100, 143, 100, 144])
        t_meta.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 20))

        # Embedded QR Code on Cover
        try:
            qr_bytes = base64.b64decode(report_data.qr_code_base64.split(",")[-1])
            qr_img_io = io.BytesIO(qr_bytes)
            qr_img = Image(qr_img_io, width=1.2 * inch, height=1.2 * inch)
            
            qr_table_data = [
                [qr_img, Paragraph("<b>Official Audit Verification QR Code</b><br/>Scan to verify authentic digital signature and SHA256 checksum on municipal registry server.<br/><i>SHA256: " + report_data.checksum_sha256[:24] + "...</i>", body_style)]
            ]
            t_qr = Table(qr_table_data, colWidths=[100, 387])
            t_qr.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t_qr)
        except Exception as exc:
            logger.warning("Could not render QR image in PDF: %s", exc)

        story.append(PageBreak())

        # ── 2. Executive Summary ──────────────────────────────────────────────
        story.append(Paragraph("1. Executive Summary", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        story.append(Paragraph(f"<b>Sanction Recommendation:</b> {summary.sanction_recommendation}", body_style))
        story.append(Spacer(1, 4))
        for p_line in summary.executive_summary_text.split("\n"):
            if p_line.strip():
                story.append(Paragraph(p_line.strip(), body_style))

        story.append(Spacer(1, 10))

        # ── 3. Building Summary ───────────────────────────────────────────────
        story.append(Paragraph("2. Building Summary", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        bld_table_data = [
            [Paragraph("Property", table_header_style), Paragraph("Value", table_header_style), Paragraph("Property", table_header_style), Paragraph("Value", table_header_style)],
            [Paragraph("Building ID", table_body_style), Paragraph(bld.building_id, table_body_style), Paragraph("Plot Area", table_body_style), Paragraph(f"{bld.plot_area} m²", table_body_style)],
            [Paragraph("Building Name", table_body_style), Paragraph(bld.building_name, table_body_style), Paragraph("Built-up Area", table_body_style), Paragraph(f"{bld.builtup_area} m²", table_body_style)],
            [Paragraph("Building Type", table_body_style), Paragraph(bld.building_type, table_body_style), Paragraph("Height", table_body_style), Paragraph(f"{bld.height} m", table_body_style)],
            [Paragraph("Occupancy", table_body_style), Paragraph(bld.occupancy, table_body_style), Paragraph("Floors", table_body_style), Paragraph(str(bld.floors), table_body_style)],
            [Paragraph("AI Classified Type", table_body_style), Paragraph(f"{cls.predicted_type} ({cls.confidence*100:.0f}%)", table_body_style), Paragraph("FSI / Coverage", table_body_style), Paragraph(f"FSI: {bld.fsi:.2f} | {bld.ground_coverage:.1f}%", table_body_style)],
        ]
        t_bld = Table(bld_table_data, colWidths=[120, 123, 120, 124])
        t_bld.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#1e293b")),
            ("BACKGROUND", (2, 0), (3, 0), colors.HexColor("#1e293b")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_bld)
        story.append(Spacer(1, 10))

        # ── 4. GIS Context ────────────────────────────────────────────────────
        story.append(Paragraph("3. GIS Context & Spatial Analysis", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        gis_table_data = [
            [Paragraph("Spatial Metric", table_header_style), Paragraph("Observation", table_header_style)],
            [Paragraph("BBMP Ward & Zone", table_body_style), Paragraph(f"{gis.ward} ({gis.ward_number or 'N/A'}) — {gis.zone}", table_body_style)],
            [Paragraph("Masterplan Land Use", table_body_style), Paragraph(gis.land_use, table_body_style)],
            [Paragraph("Nearest Road", table_body_style), Paragraph(f"{gis.road_name} ({gis.road_width} m wide)", table_body_style)],
            [Paragraph("Lake Distance & Buffer", table_body_style), Paragraph(f"{gis.lake_distance:.0f} m (In Buffer: {gis.lake_buffer})", table_body_style)],
            [Paragraph("Airport Zone & Height Limit", table_body_style), Paragraph(f"In Funnel: {gis.airport_zone} | Limit: {gis.airport_height_limit or 'Unlimited'} m", table_body_style)],
            [Paragraph("Flood Risk & Heritage Zone", table_body_style), Paragraph(f"Flood Risk: {gis.flood_risk} | Heritage Zone: {gis.heritage_zone}", table_body_style)],
        ]
        t_gis = Table(gis_table_data, colWidths=[160, 327])
        t_gis.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_gis)
        story.append(Spacer(1, 10))

        # ── 5. Compliance Summary ─────────────────────────────────────────────
        story.append(Paragraph("4. Compliance Summary", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        comp_data = [
            [Paragraph("Overall Score", table_header_style), Paragraph("Rules Checked", table_header_style), Paragraph("Passed", table_header_style), Paragraph("Failed", table_header_style), Paragraph("Warnings", table_header_style), Paragraph("Blocking", table_header_style)],
            [Paragraph(f"<b>{cmp.score:.1f}%</b>", table_body_style), Paragraph(str(cmp.rules_checked), table_body_style), Paragraph(str(cmp.passed), table_body_style), Paragraph(str(cmp.failed), table_body_style), Paragraph(str(cmp.warnings), table_body_style), Paragraph(f"<b>{cmp.blocking}</b>", table_body_style)],
        ]
        t_comp = Table(comp_data, colWidths=[81, 81, 81, 81, 81, 82])
        t_comp.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#475569")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_comp)
        story.append(Spacer(1, 10))

        # ── 6. Rule Evaluation Table ──────────────────────────────────────────
        story.append(Paragraph("5. Rule Evaluation Table", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        rule_table_data = [
            [Paragraph("Rule ID", table_header_style), Paragraph("Rule Name", table_header_style), Paragraph("Status", table_header_style), Paragraph("Severity", table_header_style), Paragraph("Clause", table_header_style)]
        ]
        for r in cmp.rule_results:
            st_color = "#16a34a" if r.status == "PASSED" else ("#dc2626" if r.status == "FAILED" else "#d97706")
            rule_table_data.append([
                Paragraph(r.rule_id, table_body_style),
                Paragraph(r.rule_name, table_body_style),
                Paragraph(f"<font color='{st_color}'><b>{r.status}</b></font>", table_body_style),
                Paragraph(r.severity, table_body_style),
                Paragraph(r.clause, table_body_style),
            ])

        t_rules = Table(rule_table_data, colWidths=[90, 140, 70, 70, 117])
        t_rules.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_rules)
        story.append(Spacer(1, 10))

        # ── 7. Recommendations ────────────────────────────────────────────────
        story.append(Paragraph("6. Prioritized Recommendations", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        if recs.total_recommendations == 0:
            story.append(Paragraph("✓ Zero compliance violations or corrective recommendations logged.", body_style))
        else:
            for item in recs.recommendations:
                p_color = "#dc2626" if item.priority == "CRITICAL" else ("#ea580c" if item.priority == "HIGH" else "#d97706")
                rec_p = Paragraph(f"<b>[{item.priority}] {item.rule_id} ({item.clause}):</b> {item.recommended_action}<br/><i>Reason: {item.explanation}</i>", body_style)
                story.append(rec_p)
                story.append(Spacer(1, 3))

        story.append(Spacer(1, 10))

        # ── 8. Decision Summary ───────────────────────────────────────────────
        story.append(Paragraph("7. Decision Summary & Action Plan", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        story.append(Paragraph("<b>Top Risk Factors:</b>", body_style))
        for rf in summary.top_risk_factors:
            story.append(Paragraph(f"• {rf}", body_style))

        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>Next Officer Action Steps:</b>", body_style))
        for step in summary.next_steps:
            story.append(Paragraph(f"1. {step}", body_style))

        story.append(Spacer(1, 10))

        # ── 9. Appendix ───────────────────────────────────────────────────────
        story.append(Paragraph("8. Appendix — GIS Dataset Provenance", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        prov_data = [
            [Paragraph("Dataset Name", table_header_style), Paragraph("Authority", table_header_style), Paragraph("License", table_header_style), Paragraph("Observation", table_header_style)]
        ]
        for ds in gis.dataset_manifest:
            prov_data.append([
                Paragraph(ds.dataset_name, table_body_style),
                Paragraph(ds.authority, table_body_style),
                Paragraph(ds.license, table_body_style),
                Paragraph(ds.observation, table_body_style),
            ])

        t_prov = Table(prov_data, colWidths=[120, 100, 80, 187])
        t_prov.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#475569")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_prov)
        story.append(Spacer(1, 10))

        # ── 10. Audit Metadata ────────────────────────────────────────────────
        story.append(Paragraph("9. Audit Metadata & Integrity Signatures", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        audit_text = (
            f"<b>Report ID:</b> {report_data.report_id}<br/>"
            f"<b>SHA256 Payload Checksum:</b> {report_data.checksum_sha256}<br/>"
            f"<b>Generation Timestamp:</b> {report_data.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>"
            f"<b>Issuing System:</b> MCRDSE Municipal Engine v{ctx.evidence_bundle.software_version}"
        )
        story.append(Paragraph(audit_text, body_style))

        # Build Document
        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()
