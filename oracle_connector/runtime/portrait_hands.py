"""Connected five-finger hands and curved nail plates from bundled CC0 anatomy."""
import math
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
import anatomy


def fit_grip_wrist(p):
    """Fit wrist translation to five anatomical finger lengths before sleeves.

    This solves pose parameters; it does not train or alter any AI weights.
    The palm depth and authored orientation remain fixed, so fitting cannot
    hide the palm behind the prop to reduce its contact error.
    """
    import numpy as np
    side=1 if p['side']=='left' else -1;prefix='l' if side==1 else 'r'
    source=anatomy.landmark(prefix+'-hand',p['presentation'])
    joints=[[anatomy.landmark(prefix+f'-finger-{k}-{j}',p['presentation']) for j in range(1,5)] for k in range(1,6)]
    axis=(joints[2][0]-source).normalized();across=(joints[1][0]-joints[4][0]).normalized()
    dorsal=-axis.cross(across).normalized()*side;target_axis=Vector(p['direction']).normalized()
    rotation=axis.rotation_difference(target_axis);current=rotation@dorsal
    current=(current-target_axis*current.dot(target_axis)).normalized()
    target=Vector(p['palm_normal']);target=(target-target_axis*target.dot(target_axis)).normalized()
    angle=math.atan2(target_axis.dot(current.cross(target)),current.dot(target))
    rotation=Quaternion(target_axis,angle)@rotation;scale=p.get('scale',1.)
    roots=np.asarray([rotation@((js[0]-source)*scale) for js in joints],dtype=float)
    bends=p['finger_curls']
    lengths=np.asarray([(js[3]-js[0]).length*scale*(2*math.sin(bends[k]/2)/bends[k] if bends[k]>1e-5 else 1.) for k,js in enumerate(joints)])
    contacts=np.asarray(p['grip_contacts']);initial=np.asarray(p['wrist']);wrist=initial.copy()
    for _ in range(18):
        vectors=contacts-roots-wrist;distances=np.linalg.norm(vectors,axis=1)
        residual=(distances-lengths)/lengths
        jacobian=-vectors[:,[0,2]]/np.maximum(distances[:,None],1e-7)/lengths[:,None]
        # Regularize the two free translation coordinates around the pose.
        jacobian=np.vstack((jacobian,np.eye(2)*3.))
        residual=np.r_[residual,(wrist-initial)[[0,2]]*3.]
        step=np.linalg.lstsq(jacobian,-residual,rcond=None)[0]*.65
        wrist[[0,2]]=initial[[0,2]]+np.clip((wrist-initial)[[0,2]]+step,-.035,.035)
    ratios=np.linalg.norm(contacts-roots-wrist,axis=1)/lengths
    if min(ratios)<.72 or max(ratios)>1.30:raise ValueError('Anatomical grip requires a different palm orientation')
    return {**p,'wrist':wrist.tolist(),'wrist_fit_length_ratios':ratios.tolist()}


def build_hand(p, skin, nail, mesh_object):
    if nail is skin:
        import bpy
        name=skin.name+'-natural-nails';existing=bpy.data.materials.get(name)
        if existing is None:
            existing=skin.copy();existing.name=name
            shader=existing.node_tree.nodes.get('Principled BSDF')
            for link in list(shader.inputs['Base Color'].links):existing.node_tree.links.remove(link)
            shader.inputs['Base Color'].default_value=tuple(min(1,v*1.1) for v in skin.diffuse_color[:3])+(1,)
            shader.inputs['Roughness'].default_value=.35
        nail=existing
    side = 1 if p['side'] == 'left' else -1
    prefix = 'l' if side == 1 else 'r'
    presentation = p['presentation']
    obj = anatomy.base_part(p['side'], presentation, skin, mesh_object)
    obj.name = 'anatomical-hand-' + p['side']
    source = anatomy.landmark(prefix+'-hand', presentation)
    joints = [[anatomy.landmark(prefix+f'-finger-{k}-{j}', presentation)
               for j in range(1, 5)] for k in range(1, 6)]
    axis = (joints[2][0]-source).normalized()
    across = (joints[1][0]-joints[4][0]).normalized()
    dorsal = -axis.cross(across).normalized()*side
    anatomy.trim(obj, source-axis*.026, axis)
    surface = BVHTree.FromPolygons([v.co for v in obj.data.vertices], [f.vertices[:] for f in obj.data.polygons])
    target_axis = Vector(p['direction']).normalized()
    rotation = axis.rotation_difference(target_axis)
    current = rotation@dorsal
    current = (current-target_axis*current.dot(target_axis)).normalized()
    target = Vector(p['palm_normal']); target -= target_axis*target.dot(target_axis)
    if target.length < .05:raise ValueError('Hand normal must be transverse to its direction')
    target.normalize()
    angle = math.atan2(target_axis.dot(current.cross(target)), current.dot(target))
    rotation = Quaternion(target_axis, angle)@rotation
    wrist = Vector(p['wrist']); scale = p.get('scale', 1.); curl = p.get('curl', .15)
    wrist_swing=target_axis.rotation_difference(Vector(p['forearm_direction']).normalized()) if 'forearm_direction' in p else None
    roots = [j[0] for j in joints]
    axes = [(j[3]-j[0]).normalized() for j in joints]
    lengths = [(j[3]-j[0]).length for j in joints]

    def pose(point, finger=None):
        point = Vector(point); candidates = []
        wrist_along=(point-source).dot(axis)
        for k in range(5):
            delta = point-roots[k]; along = delta.dot(axes[k])
            distance = (delta-axes[k]*max(0., min(lengths[k], along))).length
            candidates.append((distance, k, along))
        distance, k, along = min(candidates) if finger is None else candidates[finger]
        if along > 0 and distance < (.025 if k == 0 else .018):
            bend = p['finger_curls'][k] if 'finger_curls' in p else curl*(.4 if k == 0 else 1.+.08*(k-2))
            if bend > 1e-5:
                radius = lengths[k]/bend; theta = min(along/radius, bend*1.15)
                inward = -dorsal; inward = (inward-axes[k]*inward.dot(axes[k])).normalized()
                point += axes[k]*(radius*math.sin(theta)-along) + inward*(radius*(1-math.cos(theta)))
        delta=rotation@((point-source)*scale)
        if wrist_swing is not None and wrist_along<0:
            # Keep the cut forearm end inside its sleeve while the palm keeps
            # its independent relaxed angle. No skin strip above the cuff.
            t=min(1.,-wrist_along/.020);t=t*t*(3-2*t)
            delta=Quaternion((1,0,0,0)).slerp(wrist_swing,t)@delta
        return wrist+delta

    # A prop grip has five contact targets in the same coordinates as the
    # wrist. Swing each curled finger around its anatomical root, smoothly
    # blending through the knuckle rather than translating a detached digit.
    natural_pose=pose
    if 'grip_contacts' in p:
        contacts=[Vector(q) for q in p['grip_contacts']]
        posed_roots=[natural_pose(root,k) for k,root in enumerate(roots)]
        swings=[]
        for k in range(5):
            natural=natural_pose(joints[k][3],k)-posed_roots[k]
            wanted=contacts[k]-posed_roots[k]
            if not .72<=wanted.length/max(natural.length,1e-6)<=1.30:
                raise ValueError('Grip contact would stretch finger %d by factor %.3f; adjust wrist and prop contact' % (k+1,wanted.length/max(natural.length,1e-6)))
            swings.append((natural.rotation_difference(wanted),wanted.length/natural.length))
        def pose(point,finger=None):
            point=Vector(point)
            k=finger if finger is not None else min(range(5),key=lambda i:
                (point-roots[i]-axes[i]*max(0.,min(lengths[i],(point-roots[i]).dot(axes[i])))).length)
            delta=point-roots[k];along=delta.dot(axes[k])
            distance=(delta-axes[k]*max(0.,min(lengths[k],along))).length
            result=natural_pose(point,finger)
            if along<=0 or distance>=(.025 if k==0 else .018):return result
            # Blend at the knuckle, not over half the finger. The latter
            # produced an S-shaped bend even with gentle joint curl angles.
            t=max(0.,min(1.,along/(lengths[k]*.25)));t=t*t*(3-2*t)
            swing,stretch=swings[k]
            rotation_at=Quaternion((1,0,0,0)).slerp(swing,t)
            return posed_roots[k]+rotation_at@((result-posed_roots[k])*(1+(stretch-1)*t))

    plates = []
    for k, js in enumerate(joints):
        along = (js[3]-js[2]).normalized()
        normal = (dorsal-along*dorsal.dot(along)).normalized(); transverse = along.cross(normal).normalized()
        center = js[2].lerp(js[3], .66)
        center_hit, _, _, _ = surface.ray_cast(center+normal*.04, -normal, .08)
        if center_hit is None:raise ValueError('Nail could not be fitted to its anatomical finger')
        half_length = min(.013, (js[3]-js[2]).length*.43)+p.get('nail_length', .001)*.5
        half_width = [.0057, .0048, .0051, .0047, .0038][k]
        vertices = []; faces = []; rings = 12; sides = 20
        for layer in (0, 1):
            for ring in range(rings+1):
                t = -1+2*ring/rings; width = half_width*max(.015, (1-t*t)**.45)*(1-.12*max(t, 0))
                for j in range(sides+1):
                    u = -1+2*j/sides; q = center+along*(t*half_length)+transverse*(u*width)
                    q = center_hit+along*(t*half_length)+transverse*(u*width)
                    q += normal*(.00020+layer*.00032+.0007*(1-u*u)-.00025*t*t)
                    vertices.append(tuple(pose(q, k)))
        count = (rings+1)*(sides+1)
        for r in range(rings):
            for j in range(sides):
                a = r*(sides+1)+j; b = a+sides+1
                faces.extend([(a, b, b+1, a+1), (count+a, count+a+1, count+b+1, count+b)])
        border = list(range(sides+1))+[r*(sides+1)+sides for r in range(1,rings+1)]+[rings*(sides+1)+j for j in range(sides-1,-1,-1)]+[r*(sides+1) for r in range(rings-1,0,-1)]
        for a,b in zip(border,border[1:]+border[:1]):faces.append((a,b,b+count,a+count))
        plate = mesh_object(f'anatomical-nail-{p["side"]}-{k+1}', vertices, faces, nail)
        plate['anatomical_nail'] = True; plate['finger_index'] = k+1
        for f in plate.data.polygons:f.use_smooth=True
        plates.append(plate)
    for vertex in obj.data.vertices:vertex.co=pose(vertex.co)
    anatomy.subdivide(obj, 1)
    obj['anatomical_hand'] = True; obj['finger_count'] = 5; obj['quality_revision'] = 1
    if 'grip_contacts' in p:
        obj['grip_contact_positions']=[c for k in range(5) for c in pose(joints[k][3],k)]
        obj['grip_method']='anatomical-root-swing-with-prop-contacts'
        if 'wrist_fit_length_ratios' in p:obj['wrist_fit_length_ratios']=p['wrist_fit_length_ratios']
    return [obj, *plates]
