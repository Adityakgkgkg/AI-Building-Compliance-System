"""Corrected E2E live verification script."""
import requests, time, json, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost:8000'
FRONTEND = 'http://localhost:3000'
IFC = 'plan.ifc'
LAT, LON = 12.925, 77.5938
P = {'ifc_file': IFC, 'lat': LAT, 'lon': LON}
errors = []
warns = []

def g(u, p=None):
    t=time.perf_counter()
    try:
        r=requests.get(u, params=p, timeout=30); return r, (time.perf_counter()-t)*1000
    except Exception as e:
        return None, (time.perf_counter()-t)*1000

def po(u, j=None, f=None):
    t=time.perf_counter()
    try:
        r=requests.post(u, json=j, files=f, timeout=30); return r, (time.perf_counter()-t)*1000
    except Exception as e:
        return None, (time.perf_counter()-t)*1000

print('='*70)
print('AI BUILDING COMPLIANCE SYSTEM - FULL E2E VERIFICATION')
print('='*70)

# STEP 3
print('\n[STEP 3] APPLICATION STARTUP')
print('-'*50)
r,ms=g(BASE+'/api/v1/health')
if r and r.status_code==200: print(f'  [PASS] Backend UP ({ms:.0f}ms)')
else: print(f'  [FAIL] Backend DOWN'); errors.append('Backend not reachable')

r,ms=g(FRONTEND)
if r and r.status_code==200: print(f'  [PASS] Frontend UP ({ms:.0f}ms)')
else: print(f'  [FAIL] Frontend DOWN'); errors.append('Frontend not reachable')

# STEP 4
print('\n[STEP 4] IFC PARSER')
print('-'*50)
r,ms=g(BASE+'/api/v1/parser/health')
if r and r.status_code==200:
    d=r.json()
    print(f'  [PASS] /health ({ms:.0f}ms) ifcopenshell={d.get("ifcopenshell_version")}')
else: errors.append('Parser health failed')

with open('data/uploads/plan.ifc','rb') as fh:
    r,ms=po(BASE+'/api/v1/parser/upload', f={'file':('plan.ifc',fh,'application/octet-stream')})
if r and r.status_code==200:
    d=r.json(); bld=d.get('building_evidence',{}); st=d.get('storeys',[]); sp=d.get('spaces',[])
    print(f'  [PASS] /upload ({ms:.0f}ms)')
    print(f'    building_id={bld.get("building_id")}  name={bld.get("building_name")}')
    print(f'    type={bld.get("building_type")}  height={bld.get("height")}m  floors={bld.get("floors")}')
    print(f'    fsi={bld.get("fsi")}  coverage={bld.get("ground_coverage")}%  plot={bld.get("plot_area")}m2')
    print(f'    storeys={len(st)}  spaces={len(sp)}')
    elems = d.get('statistics',{}).get('elements',{})
    print(f'    elements: walls={elems.get("walls",0)} doors={elems.get("doors",0)} windows={elems.get("windows",0)} slabs={elems.get("slabs",0)} columns={elems.get("columns",0)} total={elems.get("total",0)}')
    if len(sp)==0: warns.append('Parser spaces_count=0 (IfcSpace entities missing from IFC file)')
else: errors.append(f'Parser upload failed: {r.status_code if r else "UNREACHABLE"}')

r,ms=g(BASE+'/api/v1/parser/metadata', {'ifc_file':IFC})
if r and r.status_code==200: print(f'  [PASS] /metadata ({ms:.0f}ms)')
else: errors.append('Parser metadata failed')

r,ms=g(BASE+'/api/v1/parser/statistics', {'ifc_file':IFC})
if r and r.status_code==200: print(f'  [PASS] /statistics ({ms:.0f}ms)')
else: errors.append('Parser statistics failed')

# STEP 6
print('\n[STEP 6] GIS ENGINE')
print('-'*50)
for ep in ['ward','zone','road','lake','airport','flood']:
    r,ms=g(BASE+'/api/v1/gis/'+ep, {'lat':LAT,'lon':LON})
    if r and r.status_code==200:
        txt = json.dumps(r.json())
        print(f'  [PASS] /gis/{ep} ({ms:.0f}ms) {txt[:70]}')
    else:
        print(f'  [FAIL] /gis/{ep} ({r.status_code if r else "UNREACHABLE"})')
        errors.append(f'GIS /{ep} failed')

# STEP 8
print('\n[STEP 8] EVIDENCE BUNDLE')
print('-'*50)
r,ms=g(BASE+'/api/v1/report/context', P)
if r and r.status_code==200:
    b=r.json()
    print(f'  [PASS] /report/context ({ms:.0f}ms)')
    print(f'    report_id={b.get("report_id")}')
    print(f'    timestamp={b.get("timestamp")}')
    print(f'    building: {b["building"]["building_id"]} / {b["building"]["building_name"]}')
    print(f'    classification: {b["classification"]["predicted_type"]} ({b["classification"]["confidence"]})')
    print(f'    gis: ward={b["gis"]["ward"]} zone={b["gis"]["zone"]} road={b["gis"]["road_width"]}m')
    c=b['compliance']
    print(f'    compliance: score={c["score"]} rules={c["rules_checked"]} pass={c["passed"]} fail={c["failed"]} warn={c["warnings"]} block={c["blocking"]}')
    for rr in c['rule_results']:
        print(f'      [{rr["status"]:8s}] {rr["rule_name"]} ({rr["severity"]})')
    print(f'    metadata: total_ms={b["metadata"]["total_collection_ms"]:.1f}')
    # Verify all sections present
    for sec in ['report_id','timestamp','building','classification','gis','compliance','metadata','software_version']:
        if sec not in b or b[sec] is None:
            errors.append(f'Evidence bundle missing: {sec}')
            print(f'    [FAIL] Missing section: {sec}')
else:
    errors.append(f'Evidence bundle failed: {r.status_code if r else "UNREACHABLE"}')
    print(f'  [FAIL] /report/context ({r.status_code if r else "UNREACHABLE"}): {r.text[:200] if r else ""}')

# STEP 11
print('\n[STEP 11] DECISION ENGINE')
print('-'*50)
for ep in ['context','recommendations','approval','risk','summary']:
    r,ms=g(BASE+'/api/v1/decision/'+ep, P)
    if r and r.status_code==200:
        print(f'  [PASS] /decision/{ep} ({ms:.0f}ms)')
        if ep=='context':
            d=r.json()
            print(f'    verdict: {d["approval"]["sanction_verdict"][:80]}')
            risk_data = d.get('risk', {})
            print(f'    risk_level: {risk_data.get("risk_level", risk_data.get("overall_risk_level", "N/A"))}')
            print(f'    recommendations: {len(d.get("recommendations",[]))}')
    else:
        errors.append(f'Decision /{ep} failed')
        print(f'  [FAIL] /decision/{ep} ({r.status_code if r else "UNREACHABLE"})')

# STEP 12
print('\n[STEP 12] REPORT GENERATION')
print('-'*50)
r,ms=po(BASE+'/api/v1/export/generate', j={'ifc_file':IFC,'lat':LAT,'lon':LON,'formats':['pdf','html','json']})
if r and r.status_code==200:
    ed=r.json(); rid=ed['report_id']
    print(f'  [PASS] /export/generate ({ms:.0f}ms)')
    print(f'    report_id={rid}')
    print(f'    available_formats={ed.get("available_formats",[])}')
    print(f'    checksum={ed.get("checksum_sha256","N/A")[:32]}...')
    # Fetch each format
    for fmt in ['pdf','html','json']:
        r2,ms2=g(BASE+f'/api/v1/export/{fmt}/{rid}')
        if r2 and r2.status_code==200:
            print(f'    [PASS] {fmt.upper()} ({ms2:.0f}ms, {len(r2.content):,} bytes)')
        else:
            st = r2.status_code if r2 else 'UNREACHABLE'
            print(f'    [FAIL] {fmt.upper()} ({st})')
            errors.append(f'{fmt.upper()} report fetch failed ({st})')
    # Audit
    r3,ms3=g(BASE+f'/api/v1/export/status/{rid}')
    if r3 and r3.status_code==200:
        print(f'    [PASS] Audit trail ({ms3:.0f}ms)')
    else:
        st = r3.status_code if r3 else 'UNREACHABLE'
        print(f'    [FAIL] Audit trail ({st})')
        errors.append(f'Audit trail fetch failed ({st})')
else:
    errors.append(f'Report generation failed ({r.status_code if r else "UNREACHABLE"})')
    print(f'  [FAIL] /export/generate: {r.text[:200] if r else "UNREACHABLE"}')

# STEP 10
print('\n[STEP 10] FRONTEND PAGES')
print('-'*50)
for pg in ['/','/upload','/gis','/dashboard']:
    r,ms=g(FRONTEND+pg)
    if r and r.status_code==200:
        print(f'  [PASS] {pg} ({ms:.0f}ms, {len(r.content):,} bytes)')
    else:
        errors.append(f'Frontend {pg} failed')
        print(f'  [FAIL] {pg} ({r.status_code if r else "UNREACHABLE"})')

# STEP 15
print('\n[STEP 15] ERROR HANDLING')
print('-'*50)
r,ms=g(BASE+'/api/v1/report/context', {'ifc_file':'nonexistent_xyz_999.ifc','lat':LAT,'lon':LON})
if r and r.status_code==503:
    print(f'  [PASS] Missing IFC -> 503 ({ms:.0f}ms) code={r.json().get("error_code")}')
else:
    st = r.status_code if r else 'UNREACHABLE'
    print(f'  [WARN] Missing IFC -> {st} (expected 503)')
    warns.append(f'Missing IFC returned {st} instead of 503')

r,ms=po(BASE+'/api/v1/parser/upload', f={'file':('bad.txt',b'NOT IFC','text/plain')})
if r and r.status_code==400:
    print(f'  [PASS] Non-IFC upload -> 400 ({ms:.0f}ms)')
else:
    st = r.status_code if r else 'UNREACHABLE'
    print(f'  [WARN] Non-IFC upload -> {st} (expected 400)')
    warns.append(f'Non-IFC upload returned {st}')

r,ms=g(BASE+'/api/v1/report/context')
if r and r.status_code==422:
    print(f'  [PASS] Missing params -> 422 ({ms:.0f}ms)')
else:
    st = r.status_code if r else 'UNREACHABLE'
    warns.append(f'Missing params returned {st}')

# STEP 13
print('\n[STEP 13] DATA FLOW INTEGRITY')
print('-'*50)
r1,_=g(BASE+'/api/v1/report/context', P); b1=r1.json() if r1 and r1.status_code==200 else {}
with open('data/uploads/plan.ifc','rb') as fh:
    r2,_=po(BASE+'/api/v1/parser/upload', f={'file':('plan.ifc',fh,'application/octet-stream')})
p2=r2.json().get('building_evidence',{}) if r2 and r2.status_code==200 else {}
all_match = True
for field in ['building_id','building_name','building_type','height','floors','fsi','ground_coverage','occupancy']:
    pv=p2.get(field); ev=b1.get('building',{}).get(field)
    if pv==ev:
        print(f'  [PASS] {field}: {pv}')
    else:
        print(f'  [FAIL] {field}: parser={pv} != evidence={ev}')
        errors.append(f'Data flow break: {field}')
        all_match = False
if all_match:
    print('  [PASS] All fields correctly propagated parser -> evidence')

# SUMMARY
print('\n' + '='*70)
print('FINAL AUDIT SUMMARY')
print('='*70)
print(f'\n  Errors:   {len(errors)}')
print(f'  Warnings: {len(warns)}')
if errors:
    print('\n  ERRORS:')
    for i,e in enumerate(errors,1): print(f'    {i}. {e}')
if warns:
    print('\n  WARNINGS:')
    for i,w in enumerate(warns,1): print(f'    {i}. {w}')
if not errors:
    print('\n  STATUS: ALL CHECKS PASSED')
print('\n' + '='*70)
