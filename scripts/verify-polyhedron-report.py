#!/usr/bin/env python3
"""Verify the published report's evidence and links, without claiming model QA."""
import argparse
import hashlib
import json
import re
import struct
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []
        self.images = []
        self.headings = 0
        self.lang = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'html':
            self.lang = attrs.get('lang')
        if tag == 'h1':
            self.headings += 1
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])
        if tag == 'img':
            self.images.append(attrs)

def jpeg_size(data):
    assert data[:2] == b'\xff\xd8', 'Expected original JPEG bytes'
    pos = 2
    while pos < len(data):
        assert data[pos] == 255, 'Invalid JPEG marker'
        while data[pos] == 255:
            pos += 1
        marker = data[pos]
        pos += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        length = struct.unpack('>H', data[pos:pos + 2])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack('>HH', data[pos + 3:pos + 7])
            return width, height
        pos += length
    raise AssertionError('JPEG dimensions missing')

def verify(root, mirror=None):
    data = json.loads((root / 'evidence.json').read_text())
    assert data['scope'] == 'single_case_screenshot_review_with_live_job_metadata'
    assert data['verdict']['fullTopology'] == 'unverified'
    assert data['verdict']['printReadiness'] == 'unverified'
    assert data['verdict']['independentBenchmark'] is False
    assert {e['id'] for e in data['evidence']} == {'R1', 'F1', 'F2', 'M1', 'M2'}
    assert len(data['evidence']) == 5
    for record in data['evidence']:
        asset = (root / record['path']).resolve()
        assert asset.is_relative_to(root.resolve())
        binary = asset.read_bytes()
        assert len(binary) == record['bytes'], record['path']
        assert hashlib.sha256(binary).hexdigest() == record['sha256'], record['path']
        assert jpeg_size(binary) == (record['width'], record['height'])
        assert record['mime'] == 'image/jpeg' and record['transformed'] is False
    geometry = data['requiredSkeleton']
    assert geometry['status'] == 'conditional_requirement_not_measurement'
    assert geometry['faces'] == geometry['hexagonalFaces'] + geometry['squareFaces'] == 18
    assert geometry['edges'] * 2 == geometry['hexagonalFaces'] * 6 + geometry['squareFaces'] * 4 == 96
    assert geometry['vertices'] - geometry['edges'] + geometry['faces'] == 2
    forge = data['forge']
    elapsed = (datetime.fromisoformat(forge['updatedAt'].replace('Z', '+00:00')) - datetime.fromisoformat(forge['createdAt'].replace('Z', '+00:00'))).total_seconds()
    assert abs(elapsed - forge['recordElapsedSeconds']) < .001
    assert forge['reportedSeconds'] == 578.9 and forge['reportedSeconds'] != elapsed
    assert forge['inputPhotoByteMatch'] is False
    assert forge['inputPhotoSha256'] != data['evidence'][0]['sha256']
    assert forge['measuredTriangles'] is None and data['meshy']['measuredTriangles'] is None
    assert 'ocena wskazuje bledy lub nie zostala ukonczona' in forge['detail']
    assert data['meshy']['uiTriangleCount'] == 3079398
    assert data['meshy']['uiVertexCount'] == 1539659
    document = Document()
    html = (root / 'index.html').read_text()
    document.feed(html)
    assert document.lang == 'pl' and document.headings == 1
    assert len(document.ids) == len(set(document.ids))
    assert len(document.images) == 5
    assert all(i.get('alt') and i.get('width') and i.get('height') for i in document.images)
    for link in document.links:
        parsed = urlsplit(link)
        if parsed.scheme:
            assert parsed.scheme == 'https' and parsed.netloc == 'github.com'
        elif parsed.path and not parsed.path.startswith('/'):
            target = (root / parsed.path).resolve()
            assert target.is_relative_to(root.resolve()) and target.is_file(), link
        elif parsed.path:
            assert parsed.path == '/', link
        elif parsed.fragment:
            assert parsed.fragment in document.ids, link
    for text in (html, (root / 'report.md').read_text()):
        assert forge['jobId'] in text
        assert 'niezweryfikowane' in text.lower() or 'niezweryfikowana' in text.lower()
        assert not re.search(r'(?:siwc_bypass|Authorization:|sk-proj-|Bearer )', text)
    if mirror:
        assert (root / 'report.md').read_bytes() == mirror.read_bytes(), 'GitHub and website report differ'
    print('PASS: five original evidence hashes, image dimensions, report/data consistency, conditional geometry arithmetic, local links and GitHub mirror.')
    print('This verifies the report package. It does not certify either 3D model or print readiness.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path('public/comparisons/polyhedron-2026-09-13'))
    parser.add_argument('--mirror', type=Path, default=Path('docs/reviews/polyhedron-2026-09-13/README.md'))
    args = parser.parse_args()
    verify(args.root, args.mirror)
