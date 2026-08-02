"""
Compare E2E outputs for different IFC files.
"""

import sys
from pathlib import Path
from app.orchestrator.service import OrchestratorService

sys.stdout.reconfigure(encoding='utf-8')


f1 = Path("data/uploads/commercial_tower.ifc")
f2 = Path("data/uploads/residential_villa.ifc")

res1 = OrchestratorService.analyze_ifc(f1.read_bytes(), "commercial_tower.ifc", 12.9250, 77.5938)
res2 = OrchestratorService.analyze_ifc(f2.read_bytes(), "residential_villa.ifc", 12.9250, 77.5938)

print("=" * 80)
print("FULL END-TO-END COMPARISON ACROSS ALL MODULES:")
print("=" * 80)


def print_summary(label, r):
    b = r.building
    c = r.classification
    comp = r.compliance
    d = r.decision
    print(f"=== {label} ({b['building_name']}) ===")
    print(
        f"1. Building:       id={b['building_id']} name='{b['building_name']}' type={b['building_type']} floors={b['floors']} height={b['height']}m builtup={b['builtup_area']}m² plot={b['plot_area']}m² fsi={b['fsi']} coverage={b['ground_coverage']}%"
    )
    print(f"2. Classification: predicted={c['predicted_type']} conf={c['confidence']} reason='{c['reason']}'")
    print(
        f"3. Compliance:     score={comp['score']} rules={comp['rules_checked']} passed={comp['passed']} failed={comp['failed']} warnings={comp['warnings']} blocking={comp['blocking']}"
    )
    for rr in comp["rule_results"]:
        print(
            f"   - [{rr['status']}] {rr['rule_name']} | Expected: {rr['expected']} | Actual: {rr['actual']} | Diff: {rr['difference']}"
        )
    print(f"4. Decision:       verdict='{d['approval']['sanction_verdict']}'")
    print(f"                   risk_level={d['risk'].get('overall_risk_level', d['risk'].get('risk_level', 'N/A'))}")

    print(f"                   recommendations={len(d['recommendations'])}")
    summ = d.get('summary', {})
    text = summ.get('executive_summary', summ.get('summary_text', str(summ)))
    print(f"                   summary='{text[:100]}...'\n")



print_summary("COMMERCIAL TOWER (6 Floors, 21m)", res1)
print_summary("RESIDENTIAL VILLA (2 Floors, 12m)", res2)
