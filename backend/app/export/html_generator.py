"""
MCRDSE Sprint 4 – HTML Report Generator
=======================================
Renders a standalone, responsive HTML municipal compliance report using Jinja2 templates.
"""

from __future__ import annotations

import logging
from jinja2 import Template

from app.export.schemas import ReportData

logger = logging.getLogger("app.export.html_generator")

_HTML_TEMPLATE_STRING = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Compliance Audit Report — {{ report.report_id }}</title>
  <style>
    :root {
      --bg: #0a0e1a;
      --card-bg: #111827;
      --text: #f1f5f9;
      --muted: #94a3b8;
      --border: rgba(148,163,184,0.15);
      --accent: #8b5cf6;
      --cyan: #06b6d4;
      --green: #10b981;
      --red: #ef4444;
      --amber: #f59e0b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 2rem 1rem;
    }
    .container { max-width: 1000px; margin: 0 auto; }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }
    h1 { font-size: 1.8rem; margin-bottom: 0.5rem; color: #fff; }
    h2 { font-size: 1.2rem; margin-bottom: 1rem; color: var(--cyan); border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }
    .subtitle { color: var(--muted); font-size: 0.9rem; margin-bottom: 1.5rem; }
    .banner {
      padding: 1rem 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      margin-bottom: 1.5rem;
    }
    .banner.APPROVED { background: rgba(16,185,129,0.15); color: var(--green); border: 1px solid rgba(16,185,129,0.3); }
    .banner.REJECTED { background: rgba(239,68,68,0.15); color: var(--red); border: 1px solid rgba(239,68,68,0.3); }
    .banner.CONDITIONAL_APPROVAL, .banner.REQUIRES_MANUAL_REVIEW { background: rgba(245,158,11,0.15); color: var(--amber); border: 1px solid rgba(245,158,11,0.3); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }
    .field-label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .field-value { font-size: 0.95rem; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; font-size: 0.85rem; }
    th, td { padding: 0.6rem 0.8rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { background: rgba(255,255,255,0.04); color: var(--muted); font-size: 0.75rem; text-transform: uppercase; }
    .badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; }
    .badge.PASSED { background: rgba(16,185,129,0.2); color: var(--green); }
    .badge.FAILED { background: rgba(239,68,68,0.2); color: var(--red); }
    .badge.WARNING { background: rgba(245,158,11,0.2); color: var(--amber); }
    .badge.CRITICAL { background: rgba(239,68,68,0.2); color: var(--red); }
    .badge.HIGH { background: rgba(249,115,22,0.2); color: #f97316; }
    .badge.MEDIUM { background: rgba(245,158,11,0.2); color: var(--amber); }
    .badge.LOW { background: rgba(148,163,184,0.2); color: var(--muted); }
    .qr-container { display: flex; align-items: center; gap: 1.5rem; background: rgba(255,255,255,0.02); padding: 1rem; border-radius: 8px; }
    .qr-container img { width: 100px; height: 100px; border-radius: 6px; }
    footer { text-align: center; font-size: 0.8rem; color: var(--muted); margin-top: 2rem; border-top: 1px solid var(--border); padding-top: 1rem; }
  </style>
</head>
<body>
  <div class="container">

    <!-- Cover / Header Card -->
    <div class="card">
      <h1>MUNICIPAL PLAN SANCTION AUDIT REPORT</h1>
      <p class="subtitle">BBMP Urban Development & Plan Sanctioning Authority | Report ID: {{ report.report_id }}</p>
      
      <div class="banner {{ ctx.approval.status_category }}">
        VERDICT: {{ ctx.approval.status_category }} — {{ ctx.approval.sanction_verdict }}
      </div>

      <div class="grid">
        <div><div class="field-label">Building Name</div><div class="field-value">{{ bld.building_name }}</div></div>
        <div><div class="field-label">Readiness Score</div><div class="field-value">{{ ctx.approval.readiness_score }} / 100</div></div>
        <div><div class="field-label">Ward / Zone</div><div class="field-value">{{ gis.ward }} ({{ gis.zone }})</div></div>
        <div><div class="field-label">Overall Risk</div><div class="field-value">{{ ctx.risk.overall_risk_level }}</div></div>
      </div>
    </div>

    <!-- Executive Summary -->
    <div class="card">
      <h2>1. Executive Summary</h2>
      <p><strong>Sanction Recommendation:</strong> {{ ctx.summary.sanction_recommendation }}</p>
      <p style="margin-top: 0.5rem; color: var(--muted);">{{ ctx.summary.executive_summary_text }}</p>
    </div>

    <!-- Building Summary -->
    <div class="card">
      <h2>2. Building Summary</h2>
      <div class="grid">
        <div><div class="field-label">IFC File</div><div class="field-value">{{ bld.ifc_file }}</div></div>
        <div><div class="field-label">Building Type</div><div class="field-value">{{ bld.building_type }}</div></div>
        <div><div class="field-label">Plot Area</div><div class="field-value">{{ bld.plot_area }} m²</div></div>
        <div><div class="field-label">Built-up Area</div><div class="field-value">{{ bld.builtup_area }} m²</div></div>
        <div><div class="field-label">Height / Floors</div><div class="field-value">{{ bld.height }} m / {{ bld.floors }} Floors</div></div>
        <div><div class="field-label">FSI / Coverage</div><div class="field-value">FSI {{ bld.fsi }} | {{ bld.ground_coverage }}%</div></div>
        <div><div class="field-label">AI Classification</div><div class="field-value">{{ cls.predicted_type }} ({{ (cls.confidence*100)|round }}%)</div></div>
      </div>
    </div>

    <!-- GIS Context -->
    <div class="card">
      <h2>3. GIS Context & Spatial Intelligence</h2>
      <div class="grid">
        <div><div class="field-label">Authority</div><div class="field-value">{{ gis.authority }}</div></div>
        <div><div class="field-label">Masterplan Land Use</div><div class="field-value">{{ gis.land_use }}</div></div>
        <div><div class="field-label">Nearest Road</div><div class="field-value">{{ gis.road_name }} ({{ gis.road_width }} m)</div></div>
        <div><div class="field-label">Lake Distance</div><div class="field-value">{{ gis.lake_distance }} m (Buffer: {{ gis.lake_buffer }})</div></div>
        <div><div class="field-label">Airport Funnel</div><div class="field-value">In Zone: {{ gis.airport_zone }} | Limit: {{ gis.airport_height_limit or 'None' }}</div></div>
        <div><div class="field-label">Flood Risk</div><div class="field-value">{{ gis.flood_risk }}</div></div>
      </div>
    </div>

    <!-- Compliance Summary -->
    <div class="card">
      <h2>4. Compliance Summary</h2>
      <div class="grid">
        <div><div class="field-label">Compliance Score</div><div class="field-value">{{ cmp.score }}%</div></div>
        <div><div class="field-label">Rules Evaluated</div><div class="field-value">{{ cmp.rules_checked }}</div></div>
        <div><div class="field-label">Passed / Failed</div><div class="field-value">{{ cmp.passed }} Passed | {{ cmp.failed }} Failed</div></div>
        <div><div class="field-label">Blocking Violations</div><div class="field-value">{{ cmp.blocking }}</div></div>
      </div>
    </div>

    <!-- Rule Evaluation Table -->
    <div class="card">
      <h2>5. Rule Evaluation Table</h2>
      <table>
        <thead>
          <tr>
            <th>Rule ID</th>
            <th>Name</th>
            <th>Status</th>
            <th>Severity</th>
            <th>Clause</th>
          </tr>
        </thead>
        <tbody>
          {% for r in cmp.rule_results %}
          <tr>
            <td><code>{{ r.rule_id }}</code></td>
            <td>{{ r.rule_name }}</td>
            <td><span class="badge {{ r.status }}">{{ r.status }}</span></td>
            <td>{{ r.severity }}</td>
            <td>{{ r.clause }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Recommendations -->
    <div class="card">
      <h2>6. Prioritized Recommendations</h2>
      {% if ctx.recommendations.total_recommendations == 0 %}
        <p>✓ Zero compliance violations or corrective actions required.</p>
      {% else %}
        {% for rec in ctx.recommendations.recommendations %}
          <div style="margin-bottom: 0.8rem;">
            <span class="badge {{ rec.priority }}">{{ rec.priority }}</span>
            <strong>{{ rec.rule_id }} ({{ rec.clause }}):</strong> {{ rec.recommended_action }}
            <div style="font-size: 0.8rem; color: var(--muted); margin-top: 0.2rem;">{{ rec.explanation }}</div>
          </div>
        {% endfor %}
      {% endif %}
    </div>

    <!-- Decision Summary & Risk -->
    <div class="card">
      <h2>7. Decision Summary & Officer Next Steps</h2>
      <p style="margin-bottom: 0.5rem;"><strong>Top Risk Factors:</strong></p>
      <ul style="margin-left: 1.2rem; color: var(--muted); margin-bottom: 1rem;">
        {% for factor in ctx.summary.top_risk_factors %}
          <li>{{ factor }}</li>
        {% endfor %}
      </ul>

      <p style="margin-bottom: 0.5rem;"><strong>Recommended Next Steps:</strong></p>
      <ol style="margin-left: 1.2rem; color: var(--muted);">
        {% for step in ctx.summary.next_steps %}
          <li>{{ step }}</li>
        {% endfor %}
      </ol>
    </div>

    <!-- Appendix (Dataset Provenance) -->
    <div class="card">
      <h2>8. Appendix — GIS Dataset Provenance</h2>
      <table>
        <thead>
          <tr>
            <th>Dataset</th>
            <th>Authority</th>
            <th>License</th>
            <th>Observation</th>
          </tr>
        </thead>
        <tbody>
          {% for ds in gis.dataset_manifest %}
          <tr>
            <td>{{ ds.dataset_name }}</td>
            <td>{{ ds.authority }}</td>
            <td>{{ ds.license }}</td>
            <td>{{ ds.observation }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Audit Metadata & QR -->
    <div class="card">
      <h2>9. Audit Metadata & Verification</h2>
      <div class="qr-container">
        <img src="{{ report.qr_code_base64 }}" alt="Verification QR Code">
        <div>
          <p><strong>SHA256 Payload Hash:</strong></p>
          <p style="font-family: monospace; font-size: 0.8rem; color: var(--cyan); word-break: break-all;">{{ report.checksum_sha256 }}</p>
          <p style="font-size: 0.8rem; color: var(--muted); margin-top: 0.4rem;">
            Generated: {{ report.generated_at }} | Engine Version: {{ ctx.evidence_bundle.software_version }}
          </p>
        </div>
      </div>
    </div>

    <footer>
      BBMP Municipal Building Compliance Reporting & Decision Support Engine © 2026
    </footer>

  </div>
</body>
</html>
"""


class HTMLReportGenerator:
    """
    Jinja2 HTML report generator for municipal compliance reports.
    """

    @staticmethod
    def generate_html(report_data: ReportData) -> str:
        """
        Render responsive HTML report string from canonical ReportData.
        """
        template = Template(_HTML_TEMPLATE_STRING)
        ctx = report_data.decision_context
        
        return template.render(
            report=report_data,
            ctx=ctx,
            bld=ctx.evidence_bundle.building,
            gis=ctx.evidence_bundle.gis,
            cmp=ctx.evidence_bundle.compliance,
            cls=ctx.evidence_bundle.classification,
        )
