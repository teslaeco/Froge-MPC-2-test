# E19 static-site validation

Run with Node.js 18 or newer:

```sh
node --test verify-site.cjs
```

The default input is `../../public-resume/dist`, relative to this directory. To validate another checkout:

```sh
FORGE_SITE_DIST=/absolute/path/to/dist node --test verify-site.cjs
```

The 20 tests exercise the actual `app.js` in a Node VM with small DOM and network fixtures. They cover successful downloads, missing manifests/chunks, same-length corruption, truncation, viewer failure cleanup, fail-closed repair exports, and integrity of both real split GLBs. The download success test also checks that a retry restores the original button label. Tests only read the site checkout.

The viewer import is replaced in memory with a stub. These checks establish application flow and GLB byte/resource integrity; they do not render WebGL, run browser download policies, verify visual appearance, or validate mesh topology. Delayed download-URL cleanup is stubbed; immediate viewer-URL cleanup is asserted.

`results.tap` contains the captured test run. `run-info.json` records the tested inputs, their hashes, and the runtime version.
