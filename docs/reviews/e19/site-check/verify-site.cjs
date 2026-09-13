#!/usr/bin/env node
'use strict';

// Read-only application-flow and GLB integrity checks. No browser or WebGL.
// Usage: node --test verify-site.cjs
// Override the checkout with FORGE_SITE_DIST=/absolute/path/to/dist.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const test = require('node:test');

const dist = process.env.FORGE_SITE_DIST || path.resolve(__dirname, '../../public-resume/dist');
const source = fs.readFileSync(path.join(dist, 'app.js'), 'utf8');
const actualManifest = JSON.parse(fs.readFileSync(path.join(dist, 'assets/E19-downloads.json')));
const actualRelease = JSON.parse(fs.readFileSync(path.join(dist, 'assets/release.json')));
const data = Buffer.from('valid model content');
const hash = crypto.createHash('sha256').update(data).digest('hex');
const entry = {
  parts: ['/assets/p1', '/assets/p2'], bytes: data.length,
  sha256: hash, mime: 'model/gltf-binary', filename: 'test.glb'
};
const validManifest = { web: entry, master: entry };

async function harness(options = {}) {
  const config = {
    manifest: validManifest, release: { model: 'E19', model_sha256: hash },
    missingManifest: false, missingPart: false, corrupt: false,
    truncate: false, failViewer: false, ...options
  };
  const nodes = new Map();
  const urls = new Map();
  const downloads = [];
  const fetches = [];
  const viewerCalls = [];
  let nextURL = 0;

  function node(id) {
    if (!nodes.has(id)) {
      nodes.set(id, {
        id, hidden: id === 'live-model', disabled: false,
        textContent: id === 'download' ? 'Download' : '',
        value: id === 'review-height' ? '200' : id === 'review-notes' ? 'Fix teeth' : '',
        files: [], dataset: id === 'download' ? { downloadModel: 'web' } : {},
        events: {}, classList: { toggle() {} },
        addEventListener(type, handler) { this.events[type] = handler; },
        focus() {}, scrollIntoView() {},
        click() { downloads.push({ name: this.download, blob: urls.get(this.href) }); }
      });
    }
    return nodes.get(id);
  }

  const context = vm.createContext({
    document: {
      hidden: false, getElementById: node,
      querySelectorAll: selector => selector === '[data-download-model]' ? [node('download')] : [],
      createElement: () => node('anchor')
    },
    Blob, Uint8Array, crypto: crypto.webcrypto,
    URL: {
      createObjectURL(blob) { const id = 'blob:fixture-' + nextURL++; urls.set(id, blob); return id; },
      revokeObjectURL(id) { urls.delete(id); }
    },
    // Prevent delayed URL cleanup from keeping the process alive. Immediate
    // cleanup in the viewer's finally block is still observed and asserted.
    setTimeout: () => 0,
    __importViewer: async () => ({
      openModel: async (...args) => {
        viewerCalls.push(args);
        assert.ok(urls.has(args[0]), 'viewer receives a live Blob URL');
        if (config.failViewer) throw new Error('viewer fixture failure');
      }
    }),
    fetch: async url => {
      fetches.push(url);
      if (url === '/assets/release.json') return { ok: !!config.release, json: async () => config.release };
      if (url === '/assets/production-audit.json') return { ok: false };
      if (url === '/assets/E19-downloads.json') {
        return { ok: !config.missingManifest, json: async () => config.manifest };
      }
      if (config.missingPart) return { ok: false };
      assert.ok(['/assets/p1', '/assets/p2'].includes(url), 'unexpected fixture request: ' + url);
      let bytes = url === '/assets/p1' ? data.subarray(0, 5) : data.subarray(5);
      if (config.corrupt && url === '/assets/p1') { bytes = Buffer.from(bytes); bytes[0] ^= 1; }
      if (config.truncate && url === '/assets/p2') bytes = bytes.subarray(1);
      return { ok: true, arrayBuffer: async () => Uint8Array.from(bytes).buffer };
    }
  });

  // Inject the viewer stub into an in-memory copy only. The site is never edited.
  const importExpression = "await import('./viewer.js')";
  assert.equal(source.split(importExpression).length - 1, 1, 'expected one viewer import');
  vm.runInContext(source.replace(importExpression, 'await __importViewer()'), context, { filename: 'app.js' });
  await new Promise(setImmediate); // Settle the initial release/audit fetches.
  return { node, config, downloads, fetches, viewerCalls, urls };
}

const flowCases = [
  ['success', {}, true],
  ['missing manifest', { missingManifest: true }, false],
  ['missing chunk', { missingPart: true }, false],
  ['same-length corrupt chunk', { corrupt: true }, false],
  ['truncated chunk', { truncate: true }, false]
];

for (const [name, options, succeeds] of flowCases) {
  test('download: ' + name, async () => {
    const h = await harness(options);
    // Include the fixed retry-label regression in the success case.
    if (succeeds) {
      h.config.missingPart = true;
      await h.node('download').events.click();
      assert.equal(h.downloads.length, 0);
      assert.notEqual(h.node('download').textContent, 'Download');
      h.config.missingPart = false;
    }
    await h.node('download').events.click();
    assert.equal(h.downloads.length, succeeds ? 1 : 0);
    assert.equal(h.node('download').disabled, false);
    if (succeeds) {
      assert.equal(h.node('download').textContent, 'Download', 'successful retry restores original label');
      assert.equal(h.downloads[0].name, 'test.glb');
      assert.deepEqual(Buffer.from(await h.downloads[0].blob.arrayBuffer()), data);
    }
  });

  test('viewer flow: ' + name, async () => {
    const h = await harness(options);
    await h.node('load-3d').events.click();
    assert.equal(h.viewerCalls.length, succeeds ? 1 : 0);
    assert.equal(h.node('load-3d').disabled, false);
    assert.equal(h.node('model-image').hidden, succeeds);
    assert.equal(h.node('live-model').hidden, !succeeds);
    assert.equal(h.urls.size, 0, 'temporary model URL was revoked');
  });
}

test('viewer failure restores static render and revokes URL', async () => {
  const h = await harness({ failViewer: true });
  await h.node('load-3d').events.click();
  assert.equal(h.viewerCalls.length, 1);
  assert.equal(h.node('live-model').hidden, true);
  assert.equal(h.node('model-image').hidden, false);
  assert.equal(h.node('load-3d').disabled, false);
  assert.equal(h.urls.size, 0);
});

const repairCases = [
  ['no release', { release: null }, false],
  ['missing hash', { release: { model: 'E19' } }, false],
  ['malformed hash', { release: { model: 'E19', model_sha256: 'wrong' } }, false],
  ['mismatched hash', { release: { model: 'E18R', model_sha256: 'a'.repeat(64) } }, false],
  ['missing manifest', { missingManifest: true }, false],
  ['malformed manifest', { manifest: { web: entry } }, false],
  ['actual release and manifest', { release: actualRelease, manifest: actualManifest }, true]
];

for (const [name, options, succeeds] of repairCases) {
  test('repair export: ' + name, async () => {
    const h = await harness(options);
    await h.node('review-form').events.submit({ preventDefault() {} });
    assert.equal(h.downloads.length, succeeds ? 1 : 0);
    if (succeeds) {
      const brief = JSON.parse(await h.downloads[0].blob.text());
      assert.equal(brief.source_sha256, actualManifest.web.sha256);
      assert.equal(brief.source_model, actualRelease.model);
      assert.equal(brief.source_download_key, 'web');
      assert.equal(brief.source_download_manifest, '/assets/E19-downloads.json');
      assert.equal(brief.generation_started, false);
      assert.equal(brief.status, 'draft_not_sent');
      assert.equal(brief.visual_acceptance, 'pending');
      assert.equal(brief.manufacturing_acceptance, 'pending');
    }
  });
}

for (const key of ['web', 'master']) {
  test('actual ' + key + ' parts: size, SHA-256, GLB header, embedded resources', () => {
    const model = actualManifest[key];
    const bytes = Buffer.concat(model.parts.map(part => fs.readFileSync(path.join(dist, part))));
    assert.equal(bytes.length, model.bytes);
    assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'), model.sha256);
    assert.equal(bytes.toString('utf8', 0, 4), 'glTF');
    assert.equal(bytes.readUInt32LE(4), 2);
    assert.equal(bytes.readUInt32LE(8), bytes.length);
    assert.equal(bytes.toString('utf8', 16, 20), 'JSON');
    const jsonLength = bytes.readUInt32LE(12);
    const gltf = JSON.parse(bytes.toString('utf8', 20, 20 + jsonLength));
    const external = [...(gltf.buffers || []), ...(gltf.images || [])]
      .filter(resource => resource.uri && !resource.uri.startsWith('data:'))
      .map(resource => resource.uri);
    assert.deepEqual(external, [], 'Blob-loaded GLB must not rely on relative external resources');
  });
}
