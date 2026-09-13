# V29: Astra remains the designer; Codex and Blender execute

The user's real v28 job cda58443-da3f-4010-96d7-88432fd3fb21 failed before a model existed.
Native D1 confirms failed state, null artifact, created 2026-09-12T02:07:07.318Z.
Screenshot: 12 requests, 2356 output/reasoning tokens, 169s AI, 0s Blender;
only get_modeling_contract and get_current_model reached MCP. The local cap is proven.
The exact earlier Code Mode failure is not recoverable from v28's filtered log.
Do not claim that a specific JavaScript error was found in that original job.

With explicit user approval for higher API cost, v29 permits 32 requests,
96000 output/reasoning tokens, five geometry builds, 1800 seconds total.
These are upper bounds, not target latency or guaranteed quality. Astra remains
gpt-6-astra high. No external AI provider or hidden paid fallback is introduced.

The actual exported revision and a concrete execution recipe accompany each
model turn. The recipe explains fresh JavaScript variables and store/load,
MCP text-block parsing, awaited builds, correct waits and actual image returns.
Only actual tool outputs are scanned for bounded Code Mode errors. Repeated
identical failures stop before another model purchase. Neither hidden reasoning,
full code nor reference pixels enter this diagnostic. The owner report exposes it.

The full offline gate now intentionally executes a real Code Mode ReferenceError,
requires it to reach the corrective instruction, then reads/persists the contract,
builds with real Blender, sees render image blocks and exports FBX. Model decisions
are scripted fixtures. This gate is not a real Astra generation or likeness test.

Optional --test-job UUID performs ONE REAL PAID generation on Oracle using the
original saved prompt, edited instructions and original images. It uses the
existing authenticated loopback queue, does not alter credentials or access,
and preserves a durable new job ID across interruption/repeated commands. It
prints its report and artifact directory. It does not fabricate a success or
automatically add the terminal trial to the Site's separate job history.

Actual paid trial was NOT run in this ChatGPT session: no authenticated browser,
Oracle SSH, direct OpenAI connection, or readable API secret is available.
Native Sites metadata/rows are readable; application requests still require the
user's sign-in. We did not bypass that requirement or install an access backdoor.

Sources inspected: official Codex MCP https://learn.chatgpt.com/docs/extend/mcp?surface=cli
and Astra model https://developers.openai.com/api/docs/models/gpt-6-astra .

Validation and publication receipts are recorded separately when complete.
