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
    return {'revision':1,'state':state,'likenessVerified':False,
        'geometry':{k:result[k] for k in ('vertices','triangles','objects') if k in result},
        'textures':result.get('texture_quality',{}),'projection':result.get('photo_projection',{}),
        'faceFit':result.get('photo_face_fit',{}),'timing':read('timing.json'),
        'visualReview':review or {'status':'not_completed','assessment_completed':False},
        'automaticQualityAccepted':False}
