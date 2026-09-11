# FORGE: image-conditioned geometry and textures

## Command to Codex

Replace the photo-generation pipeline with a real image-to-3D model. For every
uploaded subject, send the actual supplied image bytes to the generation engine.
Preserve visible face shape, pose, hair, clothing, accessories and colours as
closely as that engine supports. Support one image or up to four views of the
same subject. Do not use a prebuilt body, generic face, composition signature,
registered landmarks from another job, projected photograph or flat billboard
as an automatic substitute for image-to-3D. Keep procedural modelling available
only for text/parametric requests.

Implement Meshy 7 Ultra, native geometry without remeshing, image enhancement
disabled, preserved pose, PBR texture generation, selectable 4K/8K base colour.
Use a separate securely stored Meshy API key. Show missing configuration before
accepting a photo job. Never imply that Astra's API key also authenticates Meshy.
Never automatically repeat an ambiguous paid task submission. Persist remote
task identifiers so polling and local export retries cannot buy another model.

Import the generated geometry into Blender without replacing or sculpting the
subject. Preserve the original GLB and texture files. Export actual FBX,
OBJ+MTL+textures, STL and BLEND. Keep a separate browser preview when the original
is too large; never silently downgrade the downloadable master. Report actual
texture sizes, provenance and which exports succeeded. Missing exports and
unavailable providers must not trigger a template fallback.

Verify the protocol with varied inputs, cancellation, timeouts and corrupt
downloads. Verify native Blender import/export separately. Only claim visual
likeness after generating with a real configured engine and inspecting real
front, side and back renders. One input does not establish the hidden surfaces
or physical scale. No claim of exact 1:1 identity, superior quality to Meshy,
successful production deployment or completed generation without evidence.

## Implementation / execution record

- Architecture confirmed: previous photo path made a constrained Astra scene
  plan and built a generic anatomical template. It was not neural image-to-3D.
- Implement a new provider path and authenticated configuration, leaving existing
  text modelling and saved historical jobs available.
- Runtime account checked: no Meshy credential or local GPU was available.
  Paid neural generation and likeness review require that connection.
- API reference: https://docs.meshy.ai/en/api/image-to-3d and
  https://docs.meshy.ai/en/api/multi-image-to-3d (checked 2026-09-11).
