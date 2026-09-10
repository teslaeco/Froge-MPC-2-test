"""Bounded source-resolution export. Pixel counts are not likeness scores."""
import hashlib
import json
import struct

MAX_EDGE = 8192
MAX_PHOTO_BYTES = 2 * 1024 * 1024
MAX_TOTAL_PHOTO_BYTES = 6 * 1024 * 1024
MAX_REQUEST_BYTES = 9 * 1024 * 1024
MAX_TOTAL_PIXELS = 80 * 1024 * 1024
TEXTURE_LIMITS = (2048, 4096, 8192)


def texture_limit(value=None):
    if value is None:
        return 2048  # Existing saved jobs retain their export policy.
    if type(value) is not int or value not in TEXTURE_LIMITS:
        raise ValueError('Wybierz limit tekstur 2048, 4096 lub 8192 px.')
    return value


def fit_dimensions(width, height, limit):
    if min(width, height) < 1:
        raise ValueError('Texture has no pixels.')
    scale = min(1., limit / max(width, height))
    return max(1, round(width * scale)), max(1, round(height * scale))


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
    path = folder / 'reference-photos.json'
    references = json.loads(path.read_text()) if path.is_file() else []
    limit = max((texture_limit(p.get('textureMaxSize')) for p in references), default=2048)
    targets = []
    for image in images:
        width, height = image.size
        if not width or not height:
            continue
        primary = any(image.get(key) for key in ('anatomical_atlas', 'strand_detail', 'reference_surface'))
        edge = limit if primary or limit > 2048 else 1024
        target = fit_dimensions(width, height, edge)
        targets.append((image, (width, height), target))
    if sum(w*h for _, _, (w,h) in targets) > MAX_TOTAL_PIXELS:
        raise ValueError('Tekstury przekraczaja budzet pamieci. Wybierz 4K lub mniej zdjec; nie zmniejszono ich po cichu.')
    report = []
    for image, before, target in targets:
        if target != before:
            image.scale(*target)
        if image.has_data and (image.packed_file is None or image.is_dirty):
            image.pack()
        report.append({'name': image.name, 'source_size': list(before), 'export_size': list(target),
                       'resampled': target != before, 'upscaled': False,
                       'source_sha256': image.get('source_sha256'),
                       'contains_photographed_lighting': bool(image.get('reference_surface'))})
    return {'revision': 1, 'requested_max_edge': limit, 'textures': report,
            'upscaling_used': False, 'likeness_verified': False,
            'note': '4K/8K is a maximum texture edge, not recovered detail or render resolution.'}
