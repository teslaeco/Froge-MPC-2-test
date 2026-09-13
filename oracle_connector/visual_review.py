"""Compact visual verdicts and bounded field edits, followed by a fresh review."""
import base64
from copy import deepcopy
import json
from pathlib import Path
import shutil
import time
from photo_input import user_content, validate_photo_plan
from runtime.scene_contract import record, choice, array, parse_scene, check
from scene_repair import REPAIR_SCHEMA, apply_replacements

TEXT={'type':'string','maxLength':500}
CHANGES=deepcopy(REPAIR_SCHEMA['properties']['changes'])
CHANGES.update(minItems=0,maxItems=8)
REVIEW_SCHEMA=record({'action':choice('keep','refine'),'issues':array(TEXT,0,8),'changes':CHANGES})
LABELS=('front','three-quarter','face','side','back')
ASSETS=('scene.json','model.glb','model.blend','result.json','model.fbx','model.obj',
        'model.mtl','model-mm.stl','model.froge-scene.json','textures','review')


def copy_assets(source,destination,replace=False):
    for name in ASSETS:
        src,dst=source/name,destination/name
        if replace:
            if dst.is_dir() and not dst.is_symlink():shutil.rmtree(dst)
            else:dst.unlink(missing_ok=True)
        if src.is_dir():shutil.copytree(src,dst,dirs_exist_ok=True)
        elif src.is_file():shutil.copy2(src,dst)


def review_content(prompt,photos,folder,scene):
    content=user_content(prompt,photos)
    if isinstance(content,str):content=[{'type':'input_text','text':content}]
    content.append({'type':'input_text','text':'CURRENT VALIDATED SCENE JSON:\n'+json.dumps(scene,separators=(',',':'))})
    for label in LABELS:
        path=Path(folder)/'review'/(label+'.png')
        if path.is_symlink() or not path.is_file() or not 24<=path.stat().st_size<=2*1024*1024:
            raise ValueError('Brak poprawnego renderu do oceny wizualnej: '+label)
        data=path.read_bytes()
        if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Nieprawidlowy render PNG.')
        content += [{'type':'input_text','text':'ACTUAL EXPORTED 3D MODEL — '+label},
                    {'type':'input_image','image_url':'data:image/png;base64,'+base64.b64encode(data).decode(),'detail':'high'}]
    return content


REVIEW_PROMPT='''Compare every actual exported render with the original photos and brief.
Check silhouette, face, eyes, neck, hair scale/attachment, hands, clothing, accessories,
texture alignment and colors. Identify concrete visible faults, including doubled eyes
or floating hair. Do not accept a model merely because geometry was exported.
Return a compact verdict and at most eight field replacements in changes, never a full
scene. Each path is a JSON pointer to an existing field; value_json is the JSON-encoded
replacement. Preserve part names/kinds and the subject. Use action refine only for a
specific useful correction; keep otherwise. keep with unresolved issues is NOT acceptance.
Final acceptance requires keep, no changes and no material visible faults. List inferred
hidden surfaces separately from errors; don't claim identity or exact likeness.'''


def refine(scene,prompt,photos,folder,cancelled,generate,build,ai_seconds=0.,blender_seconds=0.,
           ai_limit=600.,blender_limit=900.,clock=time.monotonic):
    folder=Path(folder)
    report={'revision':3,'status':'not_run','refinements':0,'likeness_verified':False,
            'assessment_completed':False,'accepted':False,'reviews':[]}
    backup=None;remaining=min(240.,ai_limit-ai_seconds)
    try:
        if cancelled.is_set():raise InterruptedError('Zlecenie anulowane.')
        if remaining<15:
            report['status']='budget_exhausted';return ai_seconds,blender_seconds,report
        for iteration in range(2):
            messages=[{'role':'system','content':REVIEW_PROMPT+(' This is the final check; do not request another rebuild.' if iteration else '')},
                      {'role':'user','content':review_content(prompt,photos,folder,scene)}]
            start=clock()
            try:raw=generate(messages,REVIEW_SCHEMA,min(120.,remaining) if not iteration else remaining)
            finally:
                spent=clock()-start;ai_seconds+=spent;remaining-=spent
            if cancelled.is_set():raise InterruptedError('Zlecenie anulowane.')
            value=json.loads(raw);check(value,REVIEW_SCHEMA)
            if value['action']=='keep' and value['changes']:raise ValueError('Ocena keep nie moze zawierac poprawek.')
            report['reviews'].append({'iteration':iteration,'issues':value['issues'],'action':value['action']})
            report.update(issues=value['issues'],assessment_completed=True,
                          accepted=value['action']=='keep' and not value['issues'],
                          status='reviewed' if value['action']=='keep' and not value['issues'] else 'needs_revision')
            if value['action']=='keep' or iteration or not value['changes']:
                return ai_seconds,blender_seconds,report
            corrected=parse_scene(json.dumps(apply_replacements(scene,json.dumps({'changes':value['changes']}))),prompt)
            validate_photo_plan(corrected,photos)
            if corrected==scene:return ai_seconds,blender_seconds,report
            if blender_limit-blender_seconds<30 or remaining<15:
                report['status']='refinement_budget_exhausted';return ai_seconds,blender_seconds,report
            backup=folder/'before-refinement';backup.mkdir(exist_ok=True)
            copy_assets(folder,backup,replace=True)
            (folder/'scene.json').write_text(json.dumps(corrected),encoding='utf-8')
            start=clock()
            try:build(blender_limit-blender_seconds)
            except Exception:
                copy_assets(backup,folder,replace=True);backup=None
                raise
            finally:blender_seconds+=clock()-start
            if cancelled.is_set():raise InterruptedError('Zlecenie anulowane.')
            scene=corrected
            # An assessment of the old render never certifies a changed model.
            report.update(status='refined_requires_visual_acceptance',refinements=1,
                          original_retained=True,assessment_completed=False,accepted=False)
    except InterruptedError:
        if backup:copy_assets(backup,folder,replace=True)
        raise
    except Exception as error:
        report.update(status='original_retained' if not report['refinements'] else 'refined_requires_visual_acceptance',
                      error=str(error)[:500],accepted=False)
    finally:
        (folder/'visual-review.json').write_text(json.dumps(report,ensure_ascii=False),encoding='utf-8')
    return ai_seconds,blender_seconds,report
