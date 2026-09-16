"""Bounded source-resolution export. Pixel counts are not likeness scores."""
import hashlib
import json
import struct
import os
from pathlib import Path

MAX_EDGE = 8192
MAX_PHOTO_BYTES = 2 * 1024 * 1024
MAX_TOTAL_PHOTO_BYTES = 6 * 1024 * 1024
MAX_REQUEST_BYTES = 9 * 1024 * 1024
MAX_TOTAL_PIXELS = 80 * 1024 * 1024
MAX_EXPORT_PIXELS = 192 * 1024 * 1024
GIB = 1024 ** 3
TEXTURE_LIMITS = (2048, 4096, 8192)


def texture_limit(value=None):
    if value is None:
        return 2048  # Existing saved jobs retain their export policy.
    if type(value) is not int or value not in TEXTURE_LIMITS:
        raise ValueError('Choose a texture limit of 2048, 4096 or 8192 px.')
    return value


def fit_dimensions(width, height, limit):
    if min(width, height) < 1:
        raise ValueError('Texture has no pixels.')
    scale = min(1., limit / max(width, height))
    return max(1, round(width * scale)), max(1, round(height * scale))


def requested_edge(folder):
    path = Path(folder) / 'reference-photos.json'
    photos = json.loads(path.read_text()) if path.is_file() else []
    return max((texture_limit(p.get('textureMaxSize')) for p in photos), default=2048)


def procedural_edge(legacy_edge):
    """Evaluate authored detail at its target size; never resize source photos."""
    import bpy
    limit = bpy.context.scene.get('material_max_edge', 2048)
    return min(4096, legacy_edge * max(1, limit // 2048))


def export_memory_bytes():
    # The worker passes its actual container limit. Never trust host RAM over
    # a cgroup limit; direct Blender runs retain a conservative 4 GiB default.
    value = os.environ.get('FROGE_EXPORT_MEMORY_GIB', '4')
    if value not in ('4', '8'):
        raise ValueError('FROGE_EXPORT_MEMORY_GIB must be 4 or 8.')
    limit = int(value) * GIB
    for path in ('/sys/fs/cgroup/memory.max', '/sys/fs/cgroup/memory/memory.limit_in_bytes'):
        try:
            raw = Path(path).read_text().strip()
            if raw.isdigit(): limit = min(limit, int(raw))
        except OSError:
            pass
    return limit


def material_budget(sizes, memory_bytes):
    """Plan source RGBA float + target/encoding scratch + 1 GiB for Blender.

    This conservative estimate is not a measurement of peak RSS. All images
    are admitted before any resampling or packing changes their data.
    """
    source_pixels = sum(w*h for (w,h), _ in sizes)
    export_pixels = sum(w*h for _, (w,h) in sizes)
    estimate = GIB + source_pixels*16 + export_pixels*32
    if export_pixels > MAX_EXPORT_PIXELS or estimate > memory_bytes:
        raise ValueError('The material set needs about %.1f GiB with a %.1f GiB budget. '
                         'Choose 4K or run 8K mode on a server with enough memory. '
                         'Textures were not silently reduced.' % (estimate/GIB, memory_bytes/GIB))
    return {'source_pixels': source_pixels, 'export_pixels': export_pixels,
            'estimated_peak_bytes': estimate, 'memory_limit_bytes': memory_bytes,
            'max_export_pixels': MAX_EXPORT_PIXELS, 'estimate_is_measured_peak': False}


def geometry_digest(objects):
    """Mesh, pose, topology, UV and material assignment guard for export only."""
    digest = hashlib.sha256()
    for obj in sorted(objects, key=lambda item: item.name):
        digest.update(obj.name.encode() + b'\0')
        digest.update(struct.pack('<16d', *(x for row in obj.matrix_world for x in row)))
        for vertex in obj.data.vertices:
            digest.update(struct.pack('<3d', *vertex.co))
        for face in obj.data.polygons:
            digest.update(struct.pack('<2I', len(face.vertices), face.material_index))
            digest.update(struct.pack('<%dI' % len(face.vertices), *face.vertices))
        for layer in obj.data.uv_layers:
            digest.update(layer.name.encode() + b'\0')
            for loop in layer.data:
                digest.update(struct.pack('<2d', *loop.uv))
    return digest.hexdigest()


def export_textures(images, folder):
    limit = requested_edge(folder)
    targets = []
    for image in images:
        width, height = image.size
        if not width or not height:
            continue
        primary = any(image.get(key) for key in ('anatomical_atlas', 'strand_detail', 'reference_surface'))
        edge = limit if primary or limit > 2048 else 1024
        target = fit_dimensions(width, height, edge)
        targets.append((image, (width, height), target))
    budget = material_budget([(before, target) for _, before, target in targets], export_memory_bytes())
    report = []
    for image, before, target in targets:
        if target != before:
            image.scale(*target)
        if image.has_data and (image.packed_file is None or image.is_dirty):
            image.pack()
        report.append({'name': image.name, 'source_size': list(before), 'export_size': list(target),
                       'resampled': target != before, 'upscaled': False,
                       'origin': image.get('detail_origin', 'source_or_legacy'),
                       'color_space': image.colorspace_settings.name,
                       'source_sha256': image.get('source_sha256'),
                       'contains_photographed_lighting': bool(image.get('reference_surface'))})
    actual_max_edge = max((max(item['export_size']) for item in report), default=0)
    source_max_edge = max((max(item['source_size']) for item in report), default=0)
    downsampled_count = sum(item['resampled'] for item in report)
    return {'revision': 3, 'requested_max_edge': limit,
            'actual_max_export_edge': actual_max_edge, 'actual_max_source_edge': source_max_edge,
            'reaches_requested_max_edge': bool(report) and actual_max_edge >= limit,
            'texture_count': len(report), 'downsampled_count': downsampled_count,
            'textures': report, 'memory_budget': budget,
            'upscaling_used': False, 'likeness_verified': False,
            'note': '4K/8K is a maximum texture edge, not recovered detail or render resolution. '
                    'actual_max_export_edge reports what is really present in this export.'}
