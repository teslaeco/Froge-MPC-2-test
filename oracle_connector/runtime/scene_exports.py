"""Portable exports of the completed master, with explicit partial failures."""
from contextlib import contextmanager
import hashlib
import math
import re
from pathlib import Path
from array import array


def _file_record(path, output):
    data = path.read_bytes()
    if not data:
        raise ValueError('Exporter produced an empty file: ' + path.name)
    return {'path': path.relative_to(output).as_posix(), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


@contextmanager
def _portable_uvs(bpy, report):
    """FBX's native exporter does not write node UVSet names. Put colour first."""
    meshes=[]
    def colour_uv(socket, depth=0):
        if depth>8 or not socket.is_linked:return None
        node=socket.links[0].from_node
        if node.type=='TEX_IMAGE':
            links=node.inputs['Vector'].links
            return links[0].from_node.uv_map if links and links[0].from_node.type=='UVMAP' else None
        for value in node.inputs:
            name=colour_uv(value,depth+1)
            if name:return name
        return None
    try:
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH' or len(obj.data.uv_layers)<2:continue
            default=next((uv.name for uv in obj.data.uv_layers if uv.active_render),obj.data.uv_layers.active.name)
            bindings=[]
            for material in obj.data.materials:
                shader=material.node_tree.nodes.get('Principled BSDF') if material and material.use_nodes else None
                name=colour_uv(shader.inputs['Base Color']) if shader else None
                bindings.append(name if name and name in obj.data.uv_layers else default)
            distinct=set(bindings)
            combine=len(distinct)>1
            primary='ExportColourUV' if combine else next(iter(distinct),default)
            if not combine and primary==obj.data.uv_layers[0].name:continue
            original=obj.data;mesh=original.copy();meshes.append((obj,original,mesh));obj.data=mesh
            layers=[]
            for uv in mesh.uv_layers:
                data=array('f',[0.])* (2*len(mesh.loops));uv.data.foreach_get('uv',data)
                layers.append((uv.name,data))
            if combine:
                # FBX/OBJ use one primary colour UV channel. Consolidate each
                # polygon's own colour UVs; retain originals for other maps.
                maps=dict(layers);merged=array('f',[0.])*(2*len(mesh.loops))
                for polygon in mesh.polygons:
                    selected=bindings[polygon.material_index] if polygon.material_index<len(bindings) else default
                    data=maps[selected]
                    for loop in polygon.loop_indices:merged[2*loop:2*loop+2]=data[2*loop:2*loop+2]
                primary='ExportColourUV'
                while primary in maps:primary+='-export'
                layers.append((primary,merged))
            # Removing a layer can invalidate the remaining RNA references.
            # Resolve each layer from the live collection before removing it.
            while mesh.uv_layers:mesh.uv_layers.remove(mesh.uv_layers[0])
            for name,data in sorted(layers,key=lambda entry:entry[0]!=primary):
                uv=mesh.uv_layers.new(name=name);uv.data.foreach_set('uv',data)
            mesh.uv_layers.active_index=0;mesh.uv_layers[0].active_render=True
            report['uv_order_changes'].append({'object':obj.name,'primary':primary,
                'per_face_colour_uvs_consolidated':combine,
                'other_uv_channels_preserved':True,'all_shader_uv_bindings_verified':False})
        yield
    finally:
        for obj,original,mesh in meshes:
            obj.data=original;bpy.data.meshes.remove(mesh)


@contextmanager
def _baked_base_colors(bpy, report):
    """Flatten anatomical skin colour for formats without glTF COLOR_0.

    Only colour is baked, with an emission pass: no new scene lighting.
    The original shader, material slots and render settings survive export.
    """
    scene = bpy.context.scene
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    settings = (scene.render.engine, scene.cycles.samples, scene.render.bake.margin)
    slots, materials, images = [], [], []
    try:
        for obj in list(scene.objects):
            # The authored anatomy has an existing non-overlapping skin atlas.
            # Projected garment UVs can overlap and need a separate unwrap;
            # baking those here would silently overwrite colour at the seams.
            if obj.type != 'MESH' or not obj.get('anatomical_head') or len(obj.material_slots) != 1:continue
            for slot in obj.material_slots:
                original = slot.material
                if not original or not original.use_nodes:continue
                shader = original.node_tree.nodes.get('Principled BSDF')
                if not shader or not shader.inputs['Base Color'].is_linked:continue
                source = shader.inputs['Base Color'].links[0].from_socket
                if source.node.type not in {'MIX_RGB', 'MIX'}:continue
                if not obj.data.uv_layers:
                    raise ValueError('Mixed base colour requires UVs: ' + obj.name)
                material = original.copy();materials.append(material)
                slots.append((slot, original));slot.material = material
                nodes, links = material.node_tree.nodes, material.node_tree.links
                shader = nodes.get('Principled BSDF')
                source = shader.inputs['Base Color'].links[0].from_socket
                output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
                surface = output.inputs['Surface'].links[0].from_socket
                emission = nodes.new('ShaderNodeEmission')
                links.new(source,emission.inputs['Color']);links.new(emission.outputs[0],output.inputs['Surface'])
                size = max([2048]+[max(n.image.size) for n in nodes if n.type == 'TEX_IMAGE' and n.image])
                size = min(size,4096)
                image = bpy.data.images.new('baked-base-color-'+obj.name,width=size,height=size,alpha=False)
                images.append(image)
                target = nodes.new('ShaderNodeTexImage');target.image = image;nodes.active = target
                bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                scene.render.engine = 'CYCLES';scene.cycles.samples = 1;scene.render.bake.margin = 8
                status = bpy.ops.object.bake(type='EMIT')
                if status != {'FINISHED'}:raise ValueError('Base-colour bake failed: '+obj.name)
                links.new(surface,output.inputs['Surface']);nodes.remove(emission)
                links.new(target.outputs['Color'],shader.inputs['Base Color'])
                image.pack()
                report['baked_base_colors'].append({'object':obj.name,'material':original.name,
                    'size':[size,size],'pass':'EMIT','scene_lighting_baked':False,
                    'reference_lighting_removed':False,'other_shader_channels_baked':False})
        yield
    finally:
        for slot, original in slots:slot.material = original
        for material in materials:bpy.data.materials.remove(material)
        for image in images:bpy.data.images.remove(image)
        scene.render.engine, scene.cycles.samples, scene.render.bake.margin = settings
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected:obj.select_set(True)
        bpy.context.view_layer.objects.active = active


@contextmanager
def _portable_images(bpy, output, report):
    """Bind temporary file images during export; restore original nodes afterward.

    Empty paths alias unrelated FBX maps. OBJ cannot copy packed images.
    """
    materials = {m for o in bpy.context.scene.objects if o.type == 'MESH'
                 for m in o.data.materials if m and m.use_nodes}
    images = {n.image for m in materials for n in m.node_tree.nodes
              if n.type == 'TEX_IMAGE' and n.image}
    original = []
    temporary = []
    try:
        folder = output / 'textures'
        folder.mkdir(exist_ok=True)
        for index, image in enumerate(sorted(images, key=lambda item: item.name)):
            if image.source not in {'FILE', 'GENERATED'} or min(image.size) < 1:
                raise ValueError('Unsupported or missing texture: ' + image.name)
            if image.packed_file is None or image.is_dirty:
                image.pack()
            if image.packed_file is None:
                raise ValueError('Texture could not be packed: ' + image.name)
            data = bytes(image.packed_file.data)
            if data.startswith(b'\x89PNG\r\n\x1a\n'):
                suffix = '.png'
            elif data.startswith(b'\xff\xd8\xff'):
                suffix = '.jpg'
            else:
                raise ValueError('Texture must be packed PNG or JPEG: ' + image.name)
            digest = hashlib.sha256(data).hexdigest()
            label = re.sub(r'[^A-Za-z0-9_-]+', '-', image.name).strip('-')[:48] or 'image'
            target = folder / ('%02d-%s-%s%s' % (index, label, digest[:12], suffix))
            target.write_bytes(data)
            # OBJ's native exporter ignores GENERATED/packed sources even with
            # a filepath. Temporarily bind ordinary file images to the same nodes.
            portable = bpy.data.images.load(str(target.resolve()), check_existing=False)
            portable.colorspace_settings.name = image.colorspace_settings.name
            portable.alpha_mode = image.alpha_mode
            temporary.append(portable)
            for material in materials:
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image == image:
                        original.append((node, image))
                        node.image = portable
            report['textures'].append({**_file_record(target, output), 'image': image.name,
                                       'size': list(image.size), 'pixels_resampled': False})
        yield
    finally:
        for node, image in original:
            node.image = image
        for image in temporary:
            bpy.data.images.remove(image)


def _checked_export(report, output, key, format_name, filenames, operation):
    entry = report[key]
    try:
        # A cancelled operator must not make stale output look successful.
        for name in filenames:
            (output / name).unlink(missing_ok=True)
        status = operation()
        if status != {'FINISHED'}:
            raise RuntimeError('Export did not finish: ' + str(status))
        records = [_file_record(output / name, output) for name in filenames]
        if key == 'obj':
            for line in (output / 'model.mtl').read_text().splitlines():
                if line.startswith(('map_', 'bump ', 'disp ', 'norm ')):
                    path = (output / line.split()[-1]).resolve()
                    if not path.is_relative_to(output.resolve()) or not path.is_file():
                        raise ValueError('OBJ material references a missing texture')
        entry.update(status='ready', files=records)
        report['formats'].append(format_name)
    except Exception as error:
        for name in filenames:
            (output / name).unlink(missing_ok=True)
        entry.update(status='failed', error=str(error)[:400])


def _clean_name(name):
    """Blender suffixes imported datablocks when originals remain in memory."""
    return re.sub(r'\.\d{3}$', '', name)


def _verify_fbx_reimport(bpy, output, report):
    """Reject an FBX that Blender cannot reopen with geometry and materials.

    This is structural portability evidence only. It does not prove that every
    Blender/glTF PBR shader channel has an FBX equivalent or that the model
    visually matches a reference person.
    """
    entry = report['fbx']
    if entry.get('status') != 'ready':return
    path = output / 'model.fbx'
    before_objects=set(bpy.data.objects);before_materials=set(bpy.data.materials);before_images=set(bpy.data.images)
    source_meshes=[o for o in before_objects if o.type=='MESH']
    source_materials={_clean_name(m.name) for o in source_meshes for m in o.data.materials if m}
    source_has_uv=any(o.data.uv_layers for o in source_meshes)
    try:
        status=bpy.ops.import_scene.fbx(filepath=str(path))
        if status!={'FINISHED'}:raise ValueError('FBX reimport did not finish: '+str(status))
        imported=[o for o in bpy.data.objects if o not in before_objects]
        meshes=[o for o in imported if o.type=='MESH']
        if not meshes:raise ValueError('FBX reimport contains no mesh geometry')
        if any(not o.data.vertices or not all(math.isfinite(c) for v in o.data.vertices for c in v.co) for o in meshes):
            raise ValueError('FBX reimport contains empty or non-finite geometry')
        imported_materials={_clean_name(m.name) for o in meshes for m in o.data.materials if m}
        missing=sorted(source_materials-imported_materials)
        if missing:raise ValueError('FBX reimport lost materials: '+', '.join(missing[:8]))
        imported_uv=sum(bool(o.data.uv_layers) for o in meshes)
        if source_has_uv and not imported_uv:raise ValueError('FBX reimport lost all UV layers')
        entry.update(reimport_verified=True,reimported_meshes=len(meshes),
                     reimported_materials=len(imported_materials),uv_presence_verified=not source_has_uv or imported_uv>0,
                     pbr_shader_equivalence_verified=False,likeness_assessed=False)
    except Exception as error:
        path.unlink(missing_ok=True)
        report['formats']=[item for item in report['formats'] if item!='fbx']
        entry.update(status='failed',files=[],reimport_verified=False,error=('FBX reimport verification failed: '+str(error))[:400])
    finally:
        for obj in [o for o in list(bpy.data.objects) if o not in before_objects]:bpy.data.objects.remove(obj,do_unlink=True)
        for material in [m for m in list(bpy.data.materials) if m not in before_materials and m.users==0]:bpy.data.materials.remove(material)
        for image in [i for i in list(bpy.data.images) if i not in before_images and i.users==0]:bpy.data.images.remove(image)


def export_interchange(output, scene_source=None):
    import bpy

    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {
        'revision': 3, 'formats': [], 'same_master_scene': True, 'textures': [], 'baked_base_colors': [], 'uv_order_changes': [], 'uv_binding_limitations': [],
        'fbx': {'axis_forward': '-Z', 'axis_up': 'Y', 'textures_embedding_requested': True,
                'reimport_verified': False,
                'shader_boundary': 'FBX preserves supported image-based channels, not every Blender PBR shader',
                'rig_policy': 'Export existing armatures and animation; do not invent a rig'},
        'obj': {'mtl': 'model.mtl', 'uvs_requested': True, 'normals_requested': True,
                'reimport_verified': False,
                'shader_boundary': 'OBJ/MTL cannot reproduce every Blender or glTF PBR shader'},
        'stl': {'numeric_unit': 'millimetre', 'textures': False, 'axis_forward': '-Z', 'axis_up': 'Y',
                'print_readiness_assessed': False, 'reimport_verified': False},
        'scene_json': {'schema': 'Froge scene contract', 'present': False, 'status': 'unavailable'},
    }
    for name, format_name in (('model.glb', 'glb'), ('model.blend', 'blend')):
        path = output / name
        if path.is_file() and path.stat().st_size:
            report['formats'].append(format_name)
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    try:
        bpy.ops.object.select_all(action='SELECT')
        try:
            for name in ('model.fbx','model.obj','model.mtl'):
                (output/name).unlink(missing_ok=True)
            with _baked_base_colors(bpy,report), _portable_uvs(bpy,report), _portable_images(bpy, output, report):
                bpy.ops.object.select_all(action='SELECT')
                _checked_export(report, output, 'fbx', 'fbx', ['model.fbx'], lambda:
                    bpy.ops.export_scene.fbx(
                        filepath=str(output / 'model.fbx'), use_selection=True,
                        apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
                        axis_forward='-Z', axis_up='Y', add_leaf_bones=False,
                        bake_anim=True, path_mode='COPY', embed_textures=True))
                _checked_export(report, output, 'obj', 'obj+mtl', ['model.obj', 'model.mtl'], lambda:
                    bpy.ops.wm.obj_export(
                        filepath=str(output / 'model.obj'), export_selected_objects=True,
                        export_materials=True, export_pbr_extensions=True,
                        export_uv=True, export_normals=True,
                        forward_axis='NEGATIVE_Z', up_axis='Y', path_mode='RELATIVE'))
        except Exception as error:
            for key in ('fbx', 'obj'):
                report[key].update(status='failed', error=str(error)[:400])
        _verify_fbx_reimport(bpy,output,report)
        # STL has no unit metadata: write numeric millimetres.
        scale = 1000.0 * bpy.context.scene.unit_settings.scale_length
        _checked_export(report, output, 'stl', 'stl', ['model-mm.stl'], lambda:
            bpy.ops.wm.stl_export(
                filepath=str(output / 'model-mm.stl'), export_selected_objects=True,
                global_scale=scale, use_scene_unit=False,
                forward_axis='NEGATIVE_Z', up_axis='Y'))
        if scene_source and Path(scene_source).is_file():
            target = output / 'model.froge-scene.json'
            try:
                target.write_bytes(Path(scene_source).read_bytes())
                record = _file_record(target, output)
                report['scene_json'].update(status='ready', present=True, files=[record])
                report['formats'].append('froge-scene-json')
            except Exception as error:
                report['scene_json'].update(status='failed', error=str(error)[:400])
    finally:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active
    report['status'] = 'partial' if any(report[k].get('status') == 'failed'
                                      for k in ('fbx', 'obj', 'stl', 'scene_json')) else 'ready'
    return report
