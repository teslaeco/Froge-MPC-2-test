import { z } from 'zod'
import { createModel, specSchema } from './model'
import { getStudio, updateStudio } from './store'
import type { WebMcpToolDefinition } from '../webmcp/registry'

const common = { domain: 'visual' as const, requiresApproval: false, connectionStatus: 'CONNECTED' as const, verificationPolicy: 'Validated local parametric geometry; no manufacturing or LLM claim', outputSchema: { type: 'object', additionalProperties: true } }
export const studioTools: WebMcpToolDefinition[] = [
  { ...common, name: 'inspect_live_3d_studio', readOnly: true, description: 'Read the live editable model specification in millimetres, revision and exact mesh bounds. Supported shapes: rocket, cylinder, cone, sphere. No external AI is connected.', inputSchema: { type: 'object', properties: {}, additionalProperties: false }, execute: async () => {
    const s = getStudio(); return { state: 'PASS', spec: s.spec, revision: s.revision, qa: createModel(s.spec).qa, llmConnected: false }
  } },
  { ...common, name: 'update_live_3d_studio', readOnly: false, description: 'Update the model shown on the home page. Supply a COMPLETE specification, millimetres, and the expectedRevision read by inspect_live_3d_studio. Refuses stale edits. No arbitrary mesh generation or production.', inputSchema: { type: 'object', properties: { spec: z.toJSONSchema(specSchema), expectedRevision: { type: 'integer', minimum: 1 } }, required: ['spec', 'expectedRevision'], additionalProperties: false }, execute: async (input: unknown) => {
    const parsed = z.object({ spec: specSchema, expectedRevision: z.number().int().positive() }).strict().safeParse(input)
    if (!parsed.success) return { state: 'FAIL', errors: parsed.error.issues.map(e => e.message) }
    if (parsed.data.expectedRevision !== getStudio().revision) return { state: 'CONFLICT', revision: getStudio().revision }
    updateStudio(parsed.data.spec, 'Agent przeglądarki zmienił parametry modelu.'); return { state: 'PASS', revision: getStudio().revision, spec: getStudio().spec }
  } },
]
