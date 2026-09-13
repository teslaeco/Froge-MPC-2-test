"""Compose labelled evidence, never generate/retouch a model preview.

Usage: python build-comparison.py --candidate /abs/face.png --clay /abs/clay.png
The screenshot crop preserves the entire original four-panel comparison and its
source labels. It is explicitly identified as screenshot evidence, not a Meshy
mesh rendered under the same conditions as the candidate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--clay', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--revision', default='E17')
    args = parser.parse_args()
    for path in (args.candidate, args.clay):
        if not path.is_file():
            raise FileNotFoundError(path)
    source = ROOT / 'upload/Screenshot_20260912-205829.png'
    baseline = ROOT / 'correction-e16/after-face.png'
    font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    regular = ImageFont.truetype(font, 24)
    small = ImageFont.truetype(font, 19)
    bold = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 32)
    canvas = Image.new('RGB', (1920, 1780), '#101922')
    draw = ImageDraw.Draw(canvas)
    draw.text((36, 22), 'Meshy + FORGE / Astra + Blender', font=bold, fill='white')
    draw.text((36, 72), 'Porównanie jednego przypadku — bez rankingu ogólnej jakości', font=regular, fill='#ccd9e1')
    # All four columns, including original headers and lower attribution line.
    crop_box = (27, 1018, 834, 1363)
    panel = Image.open(source).convert('RGB').crop(crop_box)
    panel.save(OUT / 'SCREEN-COMPARISON-SOURCE.png')
    draw.text((36, 125), 'ŹRÓDŁO UŻYTKOWNIKA: Meshy / E15 / Meshy clay / E15 clay', font=regular, fill='#8ad7e2')
    placed = ImageOps.contain(panel, (1848, 680))
    canvas.paste(placed, ((1920-placed.width)//2, 170))
    draw.text((36, 862), 'Zrzut ekranu: różne kamery i oświetlenie. Nie badaliśmy pliku 3D Meshy.', font=regular, fill='#e9c997')
    y = 925
    revision = args.revision
    labels = ['E16 — render FBX', f'{revision} — render modelu', f'{revision} — geometria bez tekstur']
    images = [baseline, args.candidate, args.clay]
    for i, (label, path) in enumerate(zip(labels, images)):
        x = 24+i*636
        draw.text((x+12, y), label, font=regular, fill='white')
        im = Image.open(path).convert('RGB')
        thumb = ImageOps.contain(im, (620, 720))
        canvas.paste(thumb, (x+(620-thumb.width)//2, y+44))
    draw.text((36, 1700), 'Detale oceniaj w oryginalnych renderach. Liczba trójkątów nie mierzy podobieństwa.', font=small, fill='#c8d6e0')
    draw.text((36, 1733), 'Siwe włosy po stronie czaszki: nowa wskazówka artystyczna użytkownika.', font=small, fill='#c8d6e0')
    output_name = f'MESHY-FORGE-{revision}.png'
    canvas.save(OUT / output_name)
    manifest = {
        'type': 'labelled_evidence_contact_sheet',
        'screenshot_source': str(source),
        'screenshot_sha256': sha(source),
        'screenshot_crop_box': crop_box,
        'source_attribution': 'Meshy screenshot supplied by user; original comparison labels retained',
        'same_camera_claim': False,
        'meshy_source_mesh_inspected': False,
        'baseline': {'path': str(baseline), 'sha256': sha(baseline)},
        'candidate': {'path': str(args.candidate), 'sha256': sha(args.candidate)},
        'clay': {'path': str(args.clay), 'sha256': sha(args.clay)},
        'operations': ['crop complete comparison panel', 'proportional resize', 'label', 'compose'],
        'revision': revision,
        'output': output_name,
        'output_sha256': sha(OUT / output_name),
    }
    if args.report:
        manifest['candidate_report'] = {'path': str(args.report), 'sha256': sha(args.report)}
    (OUT / 'comparison-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    (OUT / f'comparison-{revision}-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(OUT / output_name)


if __name__ == '__main__':
    main()
