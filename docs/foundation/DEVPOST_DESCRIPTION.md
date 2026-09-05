ForgeMCP — Multi-Agent Research & Game Studio

ForgeMCP is an agent-native web platform where people and AI agents use real browser-native WebMCP tools to observe Earth, test a deterministic 8×8×8 chess engine, create verifiable 3D systems, and keep consequential decisions under human control.

Core workflow

HUMAN → COORDINATOR → SPECIALIST AGENTS → WEBMCP TOOLS → REAL DATA / ENGINE → VERIFICATION → HUMAN DECISION

What it does

ForgeMCP brings three working systems into one visible, auditable workflow:

OBSERVE — Terra Observation System

A user can select or search for an area of interest and investigate environmental change using public Earth-observation sources. Terra can retrieve location context, bounded research areas, representative satellite imagery, terrain/elevation context, hydrology signals and public hazard observations. Results return structured provenance, timestamps, confidence, uncertainty and a verification state.

Terra never presents an AI-generated picture as satellite evidence. Missing or failed provider responses remain INSUFFICIENT_DATA or NOT_CONNECTED. Observations, anomalies, hypotheses, preliminary risk alerts and verified findings are kept separate. A hypothesis is not promoted to a fact without supporting evidence and, where required, field or in-situ verification.

LEARN & COMPETE — Cube Chess 512 AI

Cube Chess 512 is a deterministic three-dimensional chess laboratory with an 8×8×8 board and 512 addressable fields. ForgeMCP uses a pinned rules engine to execute a small candidate-versus-baseline benchmark with paired seeds and side swaps. The records contain replayable legal moves, results, termination state, legality checks, a deterministic material proxy and engine provenance.

The application does not invent Elo ratings, game counts or training results. A candidate cannot be promoted merely because an agent recommends it: legality and regression gates must pass, a recorded result must exist, and literal human approval is required.

CREATE — Game and 3D Creation Studio

The Game Studio lets a person and agents configure procedural station concepts, generate deterministic low-poly glTF assets and PNG textures, inspect the exact generated geometry, compare visible results, run QA and export a manifest. It also includes a deterministic basic Capture Chess blueprint and a separate link to the playable Cube Chess 512 deployment.

Concept artwork is labelled as concept artwork. A generated prototype is not described as manufactured hardware, an original satellite product or a production-ready model.

How we built it

The public application is built with React, TypeScript, Vite and browser-based 3D rendering. Real tools are registered through:

document.modelContext.registerTool(...)

Each tool has a focused responsibility, a validated input schema, structured output, explicit error states and a traceable source or engine boundary. The coordinator is deterministic and does not claim that an LLM ran when it did not.

The live tool inventory covers system status, place and AOI handling, Terra observation and verification workflows, the pinned Cube benchmark and promotion gates, visual QA, reversible actions and guarded commerce drafts. Chrome 149+ smoke tests discover and execute the native WebMCP tools in a real browser session instead of mocking document.modelContext.

The dashboard exposes the human request, coordinator decision, active specialist, WebMCP tool, validated input, real source or engine, structured output, provenance, confidence, uncertainty, verification result, proposed action and human approval state.

The hardest challenges

The hardest problem was not adding more AI. It was defining where AI must stop.

For Terra, the authority must be the original observation, provider metadata, measurement method and verification record. For Cube, the authority must be the deterministic rules engine, legal execution and saved game result. For mutations, the authority remains the human.

A second challenge was integrating two projects that existed before the competition without presenting older work as new. The public repository therefore separates:


PRE-CHALLENGE WORK: earlier Terra data integrations, Earth-observation research, Cube rules engine, self-play experiments, 3D models and game UI.
NEW WEBMCP CHALLENGE WORK: ForgeMCP coordinator, browser-native tool registration, integrated Terra/Cube/Create workflows, structured provenance, verification timeline, approval gates, public dashboard, judge path and demo.


A third challenge was making failures honest and visible. A provider timeout, missing image, unconnected service or unsupported browser must not quietly become a fabricated answer.

Accomplishments we are proud of


A public working web application with real document.modelContext.registerTool(...) handlers.
Fifty registered central tools discoverable through the live capability inventory.
Terra workflows grounded in public providers with provenance, uncertainty and strict evidence classes.
A pinned deterministic Cube engine that executes the current-run benchmark and rejects illegal promotion paths.
Real-browser Chrome 149+ WebMCP smoke testing.
Visible PASS / WARNING / FAIL states, audit history, human approval and rollback boundaries.
A free judge path with public source code, an open-source license, run instructions and a short demonstration video.


What we learned

WebMCP is most valuable when it lets a person and an agent operate a real application together, not when it merely adds another chat box.

Small, single-purpose tools are easier to validate and audit than one oversized agent action. Structured results are safer than persuasive prose. Provenance and uncertainty must be visible at the same time as the result. Most importantly, an agent can coordinate and propose, but evidence, deterministic engines and human judgment must remain the final authorities.

Why it matters

My long-term goal is to use technology to help people and protect the environment. Terra approaches that goal through earlier investigation of water loss, rivers, lakes, terrain and environmental hazards. Cube Chess 512 approaches it through logic, spatial reasoning, competition and learning. The Creation Studio provides a practical space for turning ideas into testable visual systems.

ForgeMCP connects those directions around one principle:

AI should help humans observe, learn, create and verify — while real evidence and human decisions stay in control.

What is next

The next steps are to expand the audited Terra tool coverage, strengthen browser and regression testing, connect additional verified data adapters, run larger reproducible Cube candidate evaluations, improve accessibility and mobile performance, and keep every new mutation behind explicit approval, audit logging and rollback.

The project will continue separating observations from hypotheses and challenge-period work from earlier research. The aim is not to claim certainty where it does not exist, but to help people reach better, faster and more transparent decisions with real tools.
