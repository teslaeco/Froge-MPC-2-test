"""Hash-bound checks for the actual final files and their render/audit reports."""
from pathlib import Path
import json,hashlib,zipfile,io
root=Path(__file__).resolve().parents[1]/'print'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for fmt in ['STL','GLB']:
 a=json.loads((root/f'print-{fmt}-production-audit.json').read_text());p=root/a['source_name'];assert sha(p)==a['source_sha256'];t=a['totals_position_welded_per_object'];assert t['components_including_unused_vertices']==1 and all(t[k]==0 for k in ['boundary_edges','nonmanifold_edges_more_than_two_faces','inconsistent_winding_edges_two_faces','collapsed_edges','unused_vertices']);assert a['degenerate_triangles']==0 and a['triangles']==2120444;assert a['dimension_matches_expected_height'];rows.append({'format':fmt,'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'topology':'one closed connected component, no detected degenerate triangles or edge topology defects'})
m=json.loads((root/'print-STL-download-parts.json').read_text());joined=b''
for r in m['parts']:
 p=root/r['filename'];assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'];joined+=p.read_bytes()
assert hashlib.sha256(joined).hexdigest()==m['sha256'] and len(joined)==m['bytes']
with zipfile.ZipFile(io.BytesIO(joined)) as z:
 assert z.testzip() is None
 assert hashlib.sha256(z.read('FORGE-E19-print-candidate-200mm.stl')).hexdigest()==rows[0]['sha256']
v=json.loads((root/'print-render-verification.json').read_text());assert sha(root/v['source'])==v['source_sha256']
for r in v['views']:assert sha(root/r['path'])==r['sha256']
assert len(v['views'])==4
report={'schema':'forge.print-delivery-verification/1','files':rows,'zip_parts_reconstruction_and_crc':'passed','render_source_and_four_images_hashes':'passed','print_candidate_visual_review_passed':False,'manufacturing_ready':False,'blocking_findings':['Ragged hair after manufacturing remesh','Simplified facial and dental details','Body-to-base load path and structural support not established','Minimum feature thickness, self-intersections, slicer/toolpath and physical sample not verified'],'source_reports':['print-STL-production-audit.json','print-GLB-production-audit.json','print-build-report.json','print-connection-repair.json','print-internal-shell-cleanup.json','print-shell-stitching.json','print-render-verification.json','print-production-gate.json','README-PRINT-E19.md']}
(root/'print-final-delivery-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
