"""Small globe-aware eyelid adjustment, with no learned identity claim."""
import math


def relaxed_lid_point(position, center, strength=.20, upper_bias=0):
    x,y,z=map(float,position);cx,cy,cz=center
    dx,dz=x-cx,z-cz
    # Preserve nose, eyebrows, temples, back of head and the other orbit.
    if abs(dx)>=.023 or abs(dz)>=.020 or y>cy+.003:return x,y,z
    wx=max(0,1-(abs(dx)/.023)**4)
    wz=max(0,1-(abs(dz)/.020)**4)
    # Upper lids normally cover more of the globe than lower lids.  Keep this
    # optional so existing neutral portraits retain their established aperture.
    effective_strength=strength+(upper_bias if dz>0 else 0)
    new_z=z-dz*effective_strength*wx*wz
    globe=1-(dx/.0147)**2-((new_z-cz)/.0143)**2
    if globe>0:
        # As the lid narrows, it still has to cover the front of the globe.
        y=min(y,cy-.0152*math.sqrt(globe)-.00035*wx*wz)
    return x,y,new_z
