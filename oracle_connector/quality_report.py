"""Read-only, export-bound quality summary. Agent approval cannot bypass evidence."""
import hashlib
import json
from pathlib import Path


def _record(folder, name, limit=2*1024**2):
    path=Path(folder)/name
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size>limit:
            return {}
        value=json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value,dict) else {}
    except (ValueError,OSError):
        return {}


def acceptance_gate(folder, result=None):
    """Host gate; never runs Blender/AI, writes files or grants catalogue approval.

Photo portraits must have fresh reconstruction evidence. Text-only and nonhuman
jobs do not pretend to have a photo reference. Explicit boards require their
renderer-produced geometry/material evidence; texture pixels remain unverified.
"""
    folder=Path(folder)
    failures=[]
    result=_record(folder,'result.json') if result is None else result
    if not isinstance(result,dict): result={}
    from blender_mcp import current_candidate
    current=current_candidate(folder)
    evidence_folder=current['path'] if current else folder
    # The final outcome check separately binds the delivered result/GLB to this
    # candidate. Reading its sidecars avoids accepting an unrelated root file.
    scene=_record(evidence_folder,'scene.json')
    portrait=result.get('portrait_quality',{})
    if not isinstance(portrait,dict): portrait={}
    actual=portrait.get('actual',{})
    heads=actual.get('heads',0) if isinstance(actual,dict) else 0
    is_person=scene.get('subject_type') in ('person','portrait') or (type(heads) is int and heads>0)
    if is_person and portrait.get('structural_checks_passed') is not True:
        failures.append('portrait_structural_checks_incomplete')

    photo_manifest=folder/'reference-photos.json'
    has_photos=False
    if photo_manifest.exists() or photo_manifest.is_symlink():
        try:
            if photo_manifest.is_symlink() or photo_manifest.stat().st_size>160000:
                raise ValueError('invalid photo manifest')
            photos=json.loads(photo_manifest.read_text(encoding='utf-8'))
            if not isinstance(photos,list): raise ValueError('invalid photo manifest')
            has_photos=bool(photos)
        except (OSError,ValueError,TypeError):
            has_photos=True
            failures.append('reference_manifest_invalid')
    required_reference=(is_person and has_photos) or any(
        (p/'reference-spec.json').exists() or (p/'reference-spec.json').is_symlink()
        for p in (folder,evidence_folder))
    reconstruction={'status':'not_required','likeness_verified':False}
    if required_reference:
        from runtime.reference_reconstruction import review_report
        try:
            reconstruction=review_report(evidence_folder,result)
            if reconstruction.get('status')!='ready_for_human_review' or reconstruction.get('failures')!=[]:
                failures.append('reference_reconstruction_incomplete')
        except (OSError,ValueError,TypeError,KeyError,AttributeError):
            reconstruction={'status':'needs_correction','failures':['invalid_reference_evidence'],
                            'likeness_verified':False}
            failures.append('reference_reconstruction_incomplete')

    board=result.get('board_review',{})
    if not isinstance(board,dict): board={}
    required_board=any((p/'board-spec.json').exists() or (p/'board-spec.json').is_symlink()
                       for p in (folder,evidence_folder))
    required_board=required_board or 'expected_cells' in board or bool(board.get('failures'))
    if required_board and (board.get('passed') is not True or
            board.get('status')!='verified_geometry_and_flat_colors' or
            board.get('failures')!=[] or board.get('unverified')!=[]):
        failures.append('board_geometry_or_materials_unverified')
    return {'revision':1,'status':'blocked' if failures else 'ready_for_agent_review',
            'passed':not failures,'failures':failures,
            'referenceRequired':required_reference,'referenceReview':reconstruction,
            'boardRequired':required_board,'boardReview':board if required_board else {'status':'not_required'},
            'likenessVerified':False,'catalogueAccepted':False}


def _model_state(folder,state):
    if state!='succeeded': return {'modelStatus':'none'},{}
    from blender_mcp import completed_outcome
    outcome=completed_outcome(folder)
    gate=acceptance_gate(folder)
    if outcome:gate['modelSha256']=outcome['model_sha256']
    if outcome and outcome.get('accepted') is True and gate['passed']:
        return {'modelStatus':'reviewed','modelSha256':outcome['model_sha256']},gate
    return {'modelStatus':'draft'},gate


def model_status(folder,state):
    """Keep the job-status API shape; detailed evidence is in /quality."""
    return _model_state(folder,state)[0]


def failure_history(folder):
    """Bounded prior-attempt diagnostics, never the current model's verdict."""
    from blender_mcp import current_candidate
    folder=Path(folder);current=current_candidate(folder)
    current_path=current['path'] if current else None
    current_revision=current.get('info',{}).get('revision') if current else None
    records=[]
    for attempt in (1,2):
        record=_record(folder,'attempt-%d-error.json'%attempt)
        if record:
            records.append({'attempt':attempt,'source':'legacy_attempt','current':False,
                            'error':str(record.get('error',''))[:1200]})
    candidates=folder/'candidates'
    if candidates.is_symlink():return records
    for attempt in range(1,6):
        candidate=candidates/str(attempt)
        if candidate.is_symlink() or not candidate.is_dir():continue
        anatomy=_record(candidate,'anatomy-failure.json',256*1024)
        if not anatomy:continue
        identity=None;model=candidate/'model.glb'
        if model.is_file() and not model.is_symlink() and 20<=model.stat().st_size<=48*1024**2:
            digest=hashlib.sha256()
            with model.open('rb') as stream:
                for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
            identity=digest.hexdigest()
        summary={'code':'ANATOMY_VALIDATION','structural_checks_passed':anatomy.get('structural_checks_passed') is True}
        for key in ('expected','actual','missing','excess'):
            values=anatomy.get(key,{})
            if isinstance(values,dict):
                summary[key]={role:values[role] for role in ('heads','eyes','hands','nails')
                              if type(values.get(role)) is int}
        violations=anatomy.get('violations',[])
        summary['violations']=[{k:v[:400] if isinstance(v,str) else v
            for k,v in item.items() if k in ('code','object','message','has_uv','actual','expected')
            and (isinstance(v,str) or type(v) in (int,bool))}
            for item in violations[:12] if isinstance(item,dict)] if isinstance(violations,list) else []
        records.append({'attempt':attempt,'source':'candidate_anatomy','current':candidate==current_path,
                        'revision':current_revision if candidate==current_path else None,
                        'modelSha256':identity,'diagnostic':summary})
    return records


def quality_report(folder,state):
    folder=Path(folder)
    if folder.is_symlink(): raise ValueError('Nieprawidlowy katalog zlecenia.')
    read=lambda name:_record(folder,name)
    result=read('result.json'); review=read('visual-review.json')
    model=folder/'model.glb'
    has_model=model.is_file() and not model.is_symlink() and model.stat().st_size>=20 and bool(result)
    final,gate=_model_state(folder,state) if has_model else ({'modelStatus':'none'},{})
    validation={'scope':'current_export','modelSha256':gate.get('modelSha256'),
                'failures':gate.get('failures',[]),'portrait':result.get('portrait_quality',{})}
    effective=final['modelStatus']=='reviewed'
    agent=read('agent-outcome.json')
    # Preserve the raw attestation as provenance; consumers see effective approval.
    if agent:
        agent={**agent,'reportedAccepted':agent.get('accepted') is True,'accepted':effective}
    if review and review.get('accepted') is True and not effective:
        review={**review,'reportedAccepted':True,'accepted':False,'status':'needs_revision',
                'hostAcceptanceBlocked':True}
    return {'revision':6,'state':state,'hasModel':has_model,'likenessVerified':False,**final,
        'acceptanceGate':gate,
        'geometry':{k:result[k] for k in ('vertices','triangles','objects') if k in result},
        'textures':result.get('texture_quality',{}),'projection':result.get('photo_projection',{}),
        'faceFit':result.get('photo_face_fit',{}),'timing':read('timing.json'),
        'visualReview':review or {'status':'not_completed','assessment_completed':False},
        'failure':read('failure.json'),'validationErrors':[{'code':code,'error':code,'scope':'current_export'} for code in validation['failures']],
        'currentValidation':validation,'failureHistory':failure_history(folder),
        'agent':agent,'agentUsage':read('agent-usage.json'),
        'agentTools':read('agent-tools.json'),'agentExecution':read('agent-execution.json'),
        'executor':read('provider.json').get('executor','astra-scene'),
        'automaticQualityAccepted':effective}
