# Astra, Blender and Froge: technical findings, 2026-09-06

The observed failure was an integration contract defect. A saved Qwen script assigned
`trunk_vertices, trunk_faces = ellipsoid(...)`. Froge's helper returns a Blender Object.
The preceding material repair removed helper definitions without proving that their
callers used Froge's signatures and return types. Re-running that script could not fix
the mismatch. The model selected in the user's screenshot was still
`qwen2.5-coder:7b`, not OpenAI Astra.

## What the official demonstrations establish

[Building games with Astra](https://developers.openai.com/blog/how-to-build-games-with-astra)
describes Void Explorer and an authored Blender spacecraft. The author used generated
reference views, inspected the model's silhouette and materials, and integrated a
runtime asset into a Three.js game. The Blender source had 193 editable meshes; the
export contained 14,968 triangles in eight opaque material batches. The article reports
controlled browser measurements and explicitly distinguishes them from hardware GPU
performance. It does not report a guaranteed prompt-to-GLB duration. This is a relevant
primary source for the spacecraft workflow; the user's exact video cannot be identified
with certainty without its URL.

[Codex Modeling Studio](https://developers.openai.com/showcase/codex-modeling-studio)
is a separate web-native modeling demonstration using WebMCP. Codex inspects and edits
the scene through tools, and iterates on their capabilities and latency. This does not
mean a page with a text area automatically invokes Codex or OpenAI.

[Astra's API guide](https://developers.openai.com/api/docs/guides/latest-model)
specifies the model ID `gpt-6-astra`, Responses API support, Structured Outputs and
streaming. Reasoning `none` is unsupported; this connector uses `low`. It does not send
unsupported sampling parameters to Astra. The API generates the plan; our application
must implement and run the modeling tools and deliver the GLB. Account access and actual
latency require an authorized API key. Fast mode is not enabled here.

## Implementation decision

[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
provides schema-constrained JSON. Froge uses Responses `text.format` with
`type: json_schema`, `strict: true`, and its scene schema. This output is a scene document
for our renderer, not an autonomous multi-tool Codex session. Schema adherence does not
guarantee a useful shape: references, geometric validity and total budgets are also
checked locally. The renderer only runs fixed, tested operations; no generated Python
or expression is evaluated for a new job.

[Latency optimization](https://developers.openai.com/api/docs/guides/latency-optimization)
recommends reducing generated output and avoiding LLM work where deterministic code
suffices. Here the model specifies dimensions, materials and composition. The tested
renderer expands repeated leaves, branches and bulbs. This reduces the need to generate
thousands of tokens of Blender boilerplate on every request. No speed guarantee is
inferred from these design choices.

[Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
supports passing a schema in `format`. The optional local Qwen path uses the same contract,
but retains its CPU performance limitations. Selecting Astra requires the owner to
configure an OpenAI API key privately. Configuration never silently falls back to Qwen.

## Measured validation

These are complete **authored fixtures**, not responses from a live OpenAI model.
The actual Blender 4.3.0 runtime built and exported them, and reimported the resulting
self-contained GLBs. The oak render was inspected. Oracle currently uses Blender 4.3.2
on ARM; its complete installed path has not been exercised by this local test.

| Fixture | Build and export here | Vertices | Triangles | Mesh objects | GLB bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Oak and 20 lamps | 1.21 s | 56,306 | 57,256 | 4 | 6,215,676 |
| Rocket | 0.56 s | 263 | 490 | 9 | 372,384 |

The oak includes two embedded PNG textures and emissive lamp materials. The verifier
counts exactly 20 separate connected bulb components before export. The timings exclude
AI inference, Oracle CPU performance, network transfer, Site polling, and the review
render. A successful fixture proves the renderer can execute that plan; it does not
prove quality or timing for arbitrary future prompts.

The Site rejects new jobs on obsolete workers. Legacy geometry definitions and tuple
unpacking are rejected instead of silently rewritten. A shared AI deadline is three
minutes; invalid plans may get one repair within that deadline, and timeouts stop without
another attempt. Runtime, authentication and resource-limit checks remain in place.

## Remaining live verification

The owner must install the checked scene worker and connect an API key in the private
settings. Then measure a real Astra request from submit to downloaded GLB, and evaluate
its geometry against the request. The existing Quick Tunnel remains a test connection.
Neither a passing local fixture nor a successful update establishes customer-ready
availability or generation latency.
