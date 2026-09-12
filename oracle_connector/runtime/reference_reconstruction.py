"""Reference correction policy and evidence checks; no model-weight training.

All thresholds are per-case authoring tolerances, not medical population norms.
Missing measurements remain unknown. This module never certifies likeness.
"""
import hashlib
import json
import math
import re
import struct
import zlib
from pathlib import Path

POLICY = '''
REFERENCE RECONSTRUCTION / E17:
Preserve the last accepted head envelope and camera before a local correction.
Record observed landmarks/ratios with uncertainty; do not guess hidden anatomy.
Age is unknown unless specified or supported; grey hair is not evidence for
rescaling a skull. Distinguish living/aged/stylized skin from skeletal anatomy.
Record image sides separately from anatomical sides, including mirrored photos.
A skull can intentionally contain a recessed eye: use eye_states present for
that side, not empty_socket. Explain the requested eye in eye_states.evidence.
Review cranium, orbital rim, cheek arch, maxilla, mandible, differentiated tooth
crowns and neck continuity in neutral material before pores or colour detail.
Fit dental arches to the smile: no repeated cuboids, floating rows or lip leaks.
Hair: fit crown and root continuity first, then coherent tapered lock masses,
then fine strands; never thicken every strand to hide scalp gaps. Keep requested
left/right hair colours separate. Treat grey hair as a creative deviation when
the source is brown. Fit garment and torso together; no floating seams or skin
through cloth. Use pores/weave at physical scale, not coarse geometric noise.
Correct one named defect, reimport the exported candidate and compare front,
both profiles, back and clay against the unchanged baseline with the same camera.
Keep/revert using visible evidence; new triangles alone are not an improvement.
Subdivide only a named curvature/detail region within the actual worker budget.
Store technical lessons and failed cases, not unrelated personal conversation.
The workflow changes instructions, constraints and evaluations, not Astra weights.
'''

STAGES = ('registration', 'silhouette', 'anatomy', 'hair_cloth', 'materials', 'export_review')
REQUIRED_VIEWS = ('front', 'left', 'right', 'back', 'face_clay', 'face_textured')
AGE_GROUPS = ('unknown', 'child', 'adolescent', 'adult', 'older_adult')


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_spec(spec):
    """Validate a host-authored sidecar without changing legacy scene JSON."""
    if not isinstance(spec, dict) or spec.get('revision') != 1:
        raise ValueError('reference-spec requires revision 1')
    name = spec.get('reference_image')
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.(?:png|jpg|jpeg|webp)',name,re.IGNORECASE):
        raise ValueError('reference_image requires a safe PNG/JPEG/WebP basename in the job directory')
    if not isinstance(spec.get('reference_sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',spec['reference_sha256']):
        raise ValueError('reference_sha256 requires a lowercase SHA256 digest')
    if spec.get('age_group') not in AGE_GROUPS:
        raise ValueError('explicit age group or unknown required')
    if spec['age_group'] != 'unknown' and (not isinstance(spec.get('age_evidence'), str) or not spec['age_evidence'].strip()):
        raise ValueError('age group requires evidence; hair colour is insufficient')
    if spec.get('image_sides') not in ('frontal_unmirrored', 'frontal_mirrored', 'unknown'):
        raise ValueError('image side convention required')
    eyes = spec.get('eyes', {})
    if not isinstance(eyes, dict): raise ValueError('eyes must be an object')
    if set(eyes) != {'anatomical_left', 'anatomical_right'}:
        raise ValueError('both anatomical eye states required')
    for state in eyes.values():
        if state not in ('living_eye', 'recessed_eye_in_bone', 'empty_socket', 'occluded'):
            raise ValueError('invalid eye state')
    measures = spec.get('measurements', [])
    if not isinstance(measures, list) or len(measures) > 128:
        raise ValueError('bounded measurements list required')
    names = set()
    for measure in measures:
        if not isinstance(measure, dict): raise ValueError('measurement must be an object')
        name = measure.get('name')
        if not isinstance(name, str) or not name or name in names:
            raise ValueError('unique measurement name required')
        names.add(name)
        if not all(_finite(measure.get(k)) for k in ('reference', 'candidate', 'tolerance')):
            raise ValueError('measurements must be finite numbers')
        if measure['tolerance'] < 0 or not measure.get('unit') or not measure.get('evidence'):
            raise ValueError('measurement unit, evidence and nonnegative tolerance required')
    return spec


def compare_measurements(spec):
    return [dict(name=m['name'], error=abs(m['candidate']-m['reference']),
                 tolerance=m['tolerance'], unit=m['unit'],
                 passed=abs(m['candidate']-m['reference']) <= m['tolerance'])
            for m in validate_spec(spec).get('measurements', [])]


def expected_globes(spec):
    """Occlusion keeps the eye; only an intentional empty socket removes it."""
    return sum(s != 'empty_socket' for s in validate_spec(spec)['eyes'].values())


def chess512_checks(cells):
    """Transferred exact board contract; independent of camera or aesthetic score."""
    seen = set(); failures = []
    for c in cells:
        xyz = tuple(c.get(k) for k in ('x', 'y', 'z'))
        if any(type(n) is not int or not 0 <= n < 8 for n in xyz):
            failures.append('coordinate'); continue
        x, y, z = xyz
        if xyz in seen: failures.append('duplicate')
        seen.add(xyz)
        if type(c.get('index')) is not int or c['index'] != x+8*(y+8*z): failures.append('index')
        if type(c.get('light')) is not bool or c['light'] != ((x+y+z)&1 == 0):
            failures.append('parity')
    if len(cells) != 512 or len(seen) != 512: failures.append('cell_count')
    return {'passed': not failures, 'failures': sorted(set(failures)), 'cells': len(seen)}


def board_checks(cells, spec):
    """Measure explicit 8x8 or 8x8x8 cells, including actual assigned colour.

RGB values are linear shader colours. Image/procedural textures are unverified
here; they require a separate rendered texture-region evaluation.
"""
    if not isinstance(spec, dict) or spec.get('revision') != 1:
        raise ValueError('board-spec requires revision 1')
    size = spec.get('size')
    if size not in ([8,8,1], [8,8,8]): raise ValueError('board size must be [8,8,1] or [8,8,8]')
    for key in ('origin', 'spacing'):
        v = spec.get(key)
        if not isinstance(v, list) or len(v) != 3 or not all(_finite(n) for n in v):
            raise ValueError('board origin and spacing need three finite world coordinates')
    if any(n <= 0 for n in spec['spacing']): raise ValueError('board spacing must be positive')
    for key in ('position_tolerance', 'color_tolerance'):
        if not _finite(spec.get(key)) or not 0 <= spec[key] <= .1:
            raise ValueError('board tolerances must be explicit values from 0 to 0.1')
    for label in ('light', 'dark'):
        material = spec.get('palette', {}).get(label, {})
        rgb = material.get('linear_rgb')
        if not isinstance(material.get('material'),str) or not material['material']:
            raise ValueError('board palette requires material names')
        if not isinstance(rgb,list) or len(rgb) != 3 or not all(_finite(n) and 0 <= n <= 1 for n in rgb):
            raise ValueError('board palette requires linear_rgb in [0,1]')
    failures=[]; missing=[]; seen=set()
    for cell in cells:
        xyz=tuple(cell.get(k) for k in ('x','y','z'))
        if any(type(n) is not int or not 0 <= n < size[i] for i,n in enumerate(xyz)):
            failures.append('coordinate'); continue
        x,y,z=xyz
        if xyz in seen: failures.append('duplicate')
        seen.add(xyz)
        if type(cell.get('index')) is not int or cell['index'] != x+8*(y+8*z): failures.append('index')
        center=cell.get('center')
        if not isinstance(center,(list,tuple)) or len(center)!=3 or not all(_finite(n) for n in center):
            missing.append('cell_geometry')
        elif any(abs(center[i]-(spec['origin'][i]+xyz[i]*spec['spacing'][i])) > spec['position_tolerance'] for i in range(3)):
            failures.append('cell_position')
        label='light' if ((x+y+z)&1)==0 else 'dark'
        expected=spec['palette'][label]
        materials=cell.get('materials')
        if not isinstance(materials,list) or not materials: missing.append('cell_material'); continue
        for material in materials:
            if material.get('name') != expected['material']: failures.append('material_parity')
            rgb=material.get('linear_rgb')
            if not isinstance(rgb,(list,tuple)) or len(rgb)!=3 or not all(_finite(n) for n in rgb):
                missing.append('texture_color_requires_render_review')
            elif max(abs(a-b) for a,b in zip(rgb,expected['linear_rgb'])) > spec['color_tolerance']:
                failures.append('material_color')
    expected_count=64*size[2]
    if len(cells)!=expected_count or len(seen)!=expected_count: failures.append('cell_count')
    if not cells: missing.append('cell_evidence_missing')
    return {'status': 'unverified' if missing else 'needs_correction' if failures else 'verified_geometry_and_flat_colors',
            'passed': not failures and not missing, 'failures': sorted(set(failures)),
            'unverified': sorted(set(missing)), 'actual_cells':len(seen),'expected_cells':expected_count,
            'size':size,'texture_pixels_verified':False,'likeness_verified':False}


def _board_cells(objects):
    """Read actual Blender geometry, including consolidated boards with FACE IDs."""
    import bpy
    depsgraph=bpy.context.evaluated_depsgraph_get()
    cells=[]
    for obj in objects:
        if obj.type != 'MESH': continue
        obj=obj.evaluated_get(depsgraph)
        mesh=obj.data
        attr=mesh.attributes.get('board_cell_index')
        if attr and (attr.domain != 'FACE' or attr.data_type != 'INT'):
            raise ValueError('board_cell_index requires an INT FACE attribute')
        groups={}
        if attr:
            for p in mesh.polygons:
                index=attr.data[p.index].value
                if index >= 0: groups.setdefault(index,[]).append(p)
        elif any(k in obj for k in ('board_x','board_y','board_z')):
            if not all(type(obj.get(k)) is int for k in ('board_x','board_y','board_z')):
                raise ValueError('board object requires integer board_x/y/z')
            index=obj['board_x']+8*(obj['board_y']+8*obj['board_z'])
            groups[index]=list(mesh.polygons)
        for index,polys in groups.items():
            if not polys: continue
            points=[obj.matrix_world@mesh.vertices[i].co for i in {i for p in polys for i in p.vertices}]
            center=[(min(p[a] for p in points)+max(p[a] for p in points))*.5 for a in range(3)]
            materials=[]
            for slot in sorted({p.material_index for p in polys}):
                mat=mesh.materials[slot] if slot < len(mesh.materials) else None
                rgb=None
                if mat:
                    if not mat.use_nodes: rgb=list(mat.diffuse_color[:3])
                    else:
                        # Only a direct Principled -> active Output is measurable
                        # as a flat base colour. More complex graphs stay unknown.
                        output=next((n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output),None)
                        links=output.inputs['Surface'].links if output else []
                        shader=links[0].from_node if len(links)==1 else None
                        if shader and shader.type=='BSDF_PRINCIPLED' and not shader.inputs['Base Color'].is_linked:
                            rgb=list(shader.inputs['Base Color'].default_value[:3])
                materials.append({'name':mat.name if mat else None,'linear_rgb':rgb})
            if attr: x,y,z=index%8,(index//8)%8,index//64
            else: x,y,z=(obj[k] for k in ('board_x','board_y','board_z'))
            cells.append({'x':x,'y':y,'z':z,'index':index,'center':center,'materials':materials})
    return cells


def board_review_report(folder, objects):
    """Called by the actual worker for every draft; absent evidence never passes."""
    try:
        spec=_load_optional(folder,'board-spec.json')
        if spec is None:
            return {'status':'unverified','passed':False,'unverified':['board_spec_missing'],
                    'scope':'No board contract supplied; this is not an assertion that the job is a board.'}
        return board_checks(_board_cells(objects),spec)
    except (ValueError,TypeError,AttributeError,OSError) as error:
        return {'status':'unverified','passed':False,'unverified':['invalid_board_evidence'],
                'validation_error':str(error)[:240]}


def _load_optional(folder, name):
    path = Path(folder)/name
    if not path.exists(): return None
    if path.is_symlink() or path.stat().st_size > 256000:
        raise ValueError('invalid or oversized reconstruction sidecar')
    result = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(result, dict): raise ValueError('sidecar must be an object')
    return result


def _png_dimensions(data):
    """Bounded PNG container validation, not pixel decoding or visual grading."""
    if len(data) < 45 or data[:8] != b'\x89PNG\r\n\x1a\n': return None
    offset = 8; dimensions = None; image_data = False
    while offset + 12 <= len(data):
        length = struct.unpack('>I', data[offset:offset+4])[0]
        kind = data[offset+4:offset+8]; end = offset+8+length
        if end+4 > len(data): return None
        payload = data[offset+8:end]
        if zlib.crc32(kind+payload)&0xffffffff != struct.unpack('>I', data[end:end+4])[0]:
            return None
        if dimensions is None:
            if kind != b'IHDR' or length != 13: return None
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', payload)
            if not (128 <= width <= 8192 and 128 <= height <= 8192): return None
            if depth not in (1,2,4,8,16) or color not in (0,2,3,4,6): return None
            if compression or filtering or interlace not in (0,1): return None
            dimensions = [width, height]
        elif kind == b'IHDR': return None
        if kind == b'IDAT': image_data = image_data or length > 0
        if kind == b'IEND':
            return dimensions if length == 0 and image_data and end+4 == len(data) else None
        offset = end+4
    return None


def _reference_identity(folder, spec):
    path = Path(folder)/spec['reference_image']
    if path.is_symlink(): raise ValueError('reference_image_symlink')
    if not path.is_file(): raise ValueError('reference_image_missing')
    if not 1 <= path.stat().st_size <= 64*1024**2: raise ValueError('reference_image_size')
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2),b''): digest.update(block)
    return digest.hexdigest()


def review_report(folder, export_report):
    """Expose fail-closed review readiness alongside usable draft exports.

Evidence JSON is worker/reviewer-authored, never trusted as customer acceptance.
The host still owns catalogue approval; this gate cannot grant it.
"""
    folder = Path(folder)
    failures = []
    validation_errors = []
    try:
        spec = _load_optional(folder, 'reference-spec.json')
        if spec is not None: validate_spec(spec)
        evidence = _load_optional(folder, 'reference-evidence.json') or {}
    except (ValueError, OSError, TypeError) as error:
        spec = None; evidence = {}
        failures.append('invalid_reconstruction_sidecar')
        validation_errors.append({'code': 'invalid_reconstruction_sidecar', 'message': str(error)[:240]})
    model = folder/'model.glb'
    digest = hashlib.sha256()
    with model.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
    sha = digest.hexdigest()
    measurements = []
    reference_sha = None
    if spec is None: failures.append('reference_spec_missing')
    else:
        measurements = compare_measurements(spec)
        if not measurements: failures.append('reference_measurements_missing')
        if any(not m['passed'] for m in measurements): failures.append('reference_measurement_regression')
        try:
            reference_sha = _reference_identity(folder,spec)
            if reference_sha != spec['reference_sha256']: failures.append('reference_hash_mismatch')
            if evidence.get('reference_sha256') != reference_sha: failures.append('stale_or_missing_reference_review')
        except (OSError,ValueError) as error:
            failures.append('reference_image_unverified')
            validation_errors.append({'code':'reference_image_unverified','message':str(error)[:240]})
    if export_report.get('portrait_quality', {}).get('structural_checks_passed') is not True:
        failures.append('structural_checks_incomplete')
    if spec is not None:
        actual = export_report.get('portrait_quality', {}).get('actual', {})
        if actual.get('heads') != 1:
            failures.append('single_character_reference_required')
        elif actual.get('eyes') != expected_globes(spec):
            failures.append('reference_eye_count_unverified')
    if export_report.get('reference_socket_checks', {}).get('passed') is not True:
        failures.append('socket_checks_incomplete')
    if evidence.get('model_sha256') != sha: failures.append('stale_or_missing_review')
    if evidence.get('reimport_verified') is not True: failures.append('reimport_unverified')
    if evidence.get('same_camera_as_baseline') is not True: failures.append('camera_comparison_unverified')
    if evidence.get('critical_defects') != []: failures.append('critical_defects_unresolved')
    views = evidence.get('views', {})
    for name in REQUIRED_VIEWS:
        item = views.get(name, {}) if isinstance(views, dict) else {}
        # Fixed relative filenames; sidecars cannot read arbitrary filesystem paths.
        path = folder/'review'/('reference-'+name+'.png')
        if not isinstance(item, dict): item = {}
        valid = False
        image_sha = None
        try:
            valid = path.is_file() and not path.is_symlink() and 100 < path.stat().st_size < 64*1024**2
            if valid:
                data = path.read_bytes()
                valid = _png_dimensions(data) is not None
                image_sha = hashlib.sha256(data).hexdigest()
        except OSError:
            valid = False
        if (not valid or item.get('model_sha256') != sha or item.get('image_sha256') != image_sha
                or reference_sha is None or item.get('reference_sha256') != reference_sha
                or item.get('nonempty_verified') is not True):
            failures.append('view_missing_or_unverified:'+name)
    return {'revision': 1, 'status': 'needs_correction' if failures else 'ready_for_human_review',
            'model_sha256': sha, 'failures': failures, 'validation_errors': validation_errors,
            'reference_sha256': reference_sha,
            'measurements': measurements,
            'required_stages': list(STAGES), 'required_views': list(REQUIRED_VIEWS),
            'likeness_verified': False, 'catalogue_accepted': False,
            'evidence_scope': 'artifact hashes and explicit reviewer attestations; not automatic perceptual grading',
            'training': {'weights_updated': False, 'method': 'instructions_constraints_evaluations'}}


def refresh_review(folder):
    """Operator/host action after fresh attestations; never an automatic grader."""
    folder=Path(folder);result_path=folder/'result.json'
    if result_path.is_symlink() or not result_path.is_file() or result_path.stat().st_size>2*1024**2:
        raise ValueError('refresh requires a valid existing result.json up to 2 MiB')
    result=json.loads(result_path.read_text(encoding='utf-8'))
    if not isinstance(result,dict): raise ValueError('result.json must be an object')
    review=review_report(folder,result)
    result['reconstruction_review']=review
    for name,value in (('reconstruction-review.json',review),('result.json',result)):
        target=folder/name;pending=folder/(name+'.refresh-tmp')
        if target.is_symlink() or pending.is_symlink(): raise ValueError('refresh output cannot be a symlink')
        pending.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
        pending.replace(target)
    return review


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Refresh reference evidence metadata; not a visual grader')
    parser.add_argument('--refresh-review',type=Path,required=True,metavar='JOB_FOLDER')
    args=parser.parse_args()
    value=refresh_review(args.refresh_review)
    print(json.dumps({'status':value['status'],'failures':value['failures'],
                      'model_sha256':value['model_sha256'],'reference_sha256':value['reference_sha256']}))
