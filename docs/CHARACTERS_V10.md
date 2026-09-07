# Character generator v10

- Local anatomical neck correction tapers smoothly and protects the chin.
- Relaxed shoulder geometry; explicit tshirt, sweatshirt and hoodie choices.
- T-shirt forearms and hands share a continuous licensed anatomical mesh in standing pose.
- Buzz cuts are baked into the scalp texture instead of a raised shell.
- Cotton and denim fixed generated albedos plus packed tangent normal maps, assigned UVs before joining materials.
- Rapper example: early-2000s styling inspired by Eminem, generic adult face, no chain or hood. Not a likeness reconstruction.
- Original unpadded Shopify white logo; Amazon, eBay, AliExpress remain planned integrations.

Source example: oracle_connector/examples/rapper-eminem-style.scene.json.
Rebuild using verify_scene_runtime.py with that --scene and an --output directory; copy the verified model.glb to public/models/rapper-v10.glb.

Validation: actual Blender 4.3 export and reimport, packed images and normal maps, geometry/file budgets and full-body/detail render review. Local Blender timings exclude AI, network and Oracle. Existing saved scene descriptions retain their default short hair. Oracle worker version 10 is required for newly generated models; the static example needs no worker.

Update preserves pairing, stored OpenAI configuration and jobs. The downloaded v10 ZIP must be uploaded to Oracle Cloud Shell and applied there using the instructions shown in the studio.
