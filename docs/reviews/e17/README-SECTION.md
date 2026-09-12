## Reference-driven 3D reconstruction — E17 research work

FORGE combines reference analysis, editable Blender scenes and repeatable export checks. We are developing a workflow for game assets and custom objects such as chess sets, globes and decorative tableware. The public experience is intended to remain simple: describe an object, inspect a preview and prepare a manufacturing enquiry.

Our current character study exposes a real limitation: **the supplied Meshy result follows the reference more closely than our E15/E16 model**, especially around the eyes, smile, hair roots and clothing. Meshy is a strong complementary tool. Our approach adds explicit constraints, named editable parts, local repairs and repeatable checks; those capabilities do not by themselves establish better visual quality.

Sebastian also reported an earlier example where our workflow followed the geometry of a fan more accurately. That observation is retained as a regression case to reproduce, not presented as a measured general advantage. The goal is to combine useful approaches and improve the outcome for the artist.

The E17 work focuses on hair shape and asymmetry, anatomical connections, teeth and export fidelity. The reference remains the authority for visible features. The newly requested grey hair on the skeletal side is a deliberate art-direction change; it must not be scored as exact colour reproduction of the earlier brown-haired reference.

Our learning record stores failures, preferred revisions, reference requirements and acceptance checks. This is **application memory and evaluation work**, not a claim that the weights of OpenAI's Astra model have been retrained. OpenAI's documentation distinguishes evaluation, prompt improvements and fine-tuning as separate activities. [OpenAI model optimization](https://developers.openai.com/api/docs/guides/model-optimization)

See [the visual comparison](COMPARISON-E17.md), [the reconstruction prompt](PROMPT-E17.md), [the error catalogue](error-catalog.json) and [the production workflow](PRODUCTION-WORKFLOW.md). Model availability, tests actually run and remaining defects must be read with the accompanying E17 artifact report. A saved export or a higher polygon count does not constitute visual acceptance, animation readiness or manufacturing approval.

The intended B2B workflow quotes material usage, colours, manufacturing process and finishing before an order is accepted. A preview and a quote form are not a claim that payment, supplier assignment or physical fulfilment is already operating.
