# Face measurement assets

MediaPipe Face Landmarker float16 bundle, revision 1:
https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task

Runtime: @mediapipe/tasks-vision 0.10.21, Apache-2.0. WebAssembly files are copied
unchanged from the locked npm package. Model and implementation documentation:
https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker
https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE

Only these local files are fetched by the browser. Photographs and measurements
use the existing private job storage; no photograph is sent to Google.
The detector estimates points; it does not recover identity, hair or unseen anatomy.

SHA256:
- face_landmarker.task: 64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff
- vision_wasm_internal.js: 4a97e2520ba506c680ecd6ba6acfb146888afa0e2746d57f205352bc6ebb82eb
- vision_wasm_internal.wasm: f00ec4731faa23b3e714d00e88d4d10e2df5c0a427d3a2b4ae6e3526fdd14ef7
- vision_wasm_nosimd_internal.js: 927def7b465c51b86e4b3060f93646aca4e27121f4b8fc0483786e407ea9cf1f
- vision_wasm_nosimd_internal.wasm: 3821ea9b1f7fb8c549ef2a064ef5c85750bf375c545a49fd6eea0df44a95f1f4
