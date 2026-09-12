"""Read-only quality summary from this owner's existing job artifacts."""
import json


def quality_report(folder,state):
    if folder.is_symlink():raise ValueError('Nieprawidlowy katalog zlecenia.')
    def read(name):
        path=folder/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size>2*1024**2:return {}
        try:
            value=json.loads(path.read_text())
            return value if isinstance(value,dict) else {}
        except (ValueError,OSError):return {}
    result=read('result.json');review=read('visual-review.json')
    errors=[{'attempt':attempt,'error':str(read('attempt-%d-error.json'%attempt).get('error',''))[:1200]}
            for attempt in (1,2) if read('attempt-%d-error.json'%attempt)]
    model=folder/'model.glb'
    has_model=model.is_file() and not model.is_symlink() and model.stat().st_size>=20 and bool(result)
    return {'revision':4,'state':state,'hasModel':has_model,'likenessVerified':False,
        'geometry':{k:result[k] for k in ('vertices','triangles','objects') if k in result},
        'textures':result.get('texture_quality',{}),'projection':result.get('photo_projection',{}),
        'faceFit':result.get('photo_face_fit',{}),'timing':read('timing.json'),
        'visualReview':review or {'status':'not_completed','assessment_completed':False},
        'failure':read('failure.json'),'validationErrors':errors,
        'agent':read('agent-outcome.json'),'agentUsage':read('agent-usage.json'),
        'agentTools':read('agent-tools.json'),'agentExecution':read('agent-execution.json'),
        'executor':read('provider.json').get('executor','astra-scene'),
        'automaticQualityAccepted':review.get('accepted') is True and review.get('assessment_completed') is True}
