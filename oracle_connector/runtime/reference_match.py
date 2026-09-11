"""Recognize re-encodings of one reviewed composition, never identify a person.

The whole frame AND the face, fan and garment regions must agree. Cropping,
mirroring, a different portrait or a changed outfit disables the authored guide.
Source bytes/landmarks remain SHA-bound independently of this visual match.
"""
import json
from pathlib import Path
import numpy as np

SIGNATURE = Path(__file__).resolve().parent / 'assets/emerald-reference-signature.json'


def signature(pixels):
    height, width = pixels.shape[:2]
    # Average 25 distributed samples in each cell. Bounded working allocation;
    # independent of source resolution, with no face/background extrapolation.
    yy = (np.arange(40)[:,None] + (np.arange(5)+.5)/5) / 40
    xx = (np.arange(32)[:,None] + (np.arange(5)+.5)/5) / 32
    ys = np.minimum((yy*height).astype(int),height-1).reshape(-1)
    xs = np.minimum((xx*width).astype(int),width-1).reshape(-1)
    return pixels[ys[:,None],xs[None,:],:3].reshape(40,5,32,5,3).mean(axis=(1,3))


def compare(pixels, template=None):
    template = template or json.loads(SIGNATURE.read_text())
    height,width = pixels.shape[:2]
    if abs(width/height - template['aspect']) > .002:
        return {'matched': False, 'reason': 'different_crop_or_aspect'}
    delta = np.abs(signature(pixels)-np.asarray(template['rgb'],dtype=float))
    regions = {'frame':delta, 'face':delta[5:15,15:25],
               'fan':delta[15:28,1:22], 'garment':delta[26:40,15:30]}
    errors = {name:float(values.mean()) for name,values in regions.items()}
    accepted = all(error < .025 for error in errors.values())
    return {'matched':accepted, 'reason':'reviewed_composition' if accepted else 'different_image_content',
            'mean_absolute_rgb_error':errors, 'likeness_verified':False}


def match_image(path):
    import bpy
    image = bpy.data.images.load(str(path),check_existing=False)
    try:
        width,height=image.size
        if width*height > 80*1024*1024:
            raise ValueError('Reference exceeds decoded pixel budget.')
        pixels=np.empty(width*height*4,dtype=np.float32)
        image.pixels.foreach_get(pixels)
        result=compare(pixels.reshape(height,width,4)[::-1,:,:3])
        return result,width,height
    finally:
        bpy.data.images.remove(image)


def match_fit(fit):
    result,_,_=match_image(fit.image_path)
    if result['matched']:
        fit.guide_verified_sha256=fit.source_sha256
    fit.report['couture_guide']=result
    return result
