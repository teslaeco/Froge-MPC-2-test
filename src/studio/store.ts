import { INITIAL_SPEC, parseCommand, specSchema, type ModelSpec } from './model'

type Revision = { spec: ModelSpec; note: string }
let state = { spec: { ...INITIAL_SPEC }, revision: 1, history: [] as Revision[], note: 'Rakieta startowa: Ø 10 mm × 50 mm. Zmień wymiar lub wpisz polecenie.', errors: [] as string[] }
const subscribers = new Set<() => void>()
export const getStudio = () => state
export function subscribeStudio(callback: () => void) { subscribers.add(callback); return () => { subscribers.delete(callback) } }
function emit() { subscribers.forEach(fn => fn()) }
export function updateStudio(value: unknown, note = 'Zmieniono parametry') {
  const parsed = specSchema.safeParse(value)
  if (!parsed.success) { state = { ...state, errors: parsed.error.issues.map(x => x.message) }; emit(); return false }
  if (JSON.stringify(state.spec) === JSON.stringify(parsed.data)) {
    state = { ...state, errors: [], note }; emit(); return true
  }
  state = { spec: parsed.data, revision: state.revision + 1, history: [...state.history, { spec: state.spec, note: state.note }].slice(-30), note, errors: [] }
  emit(); return true
}
export function applyStudioCommand(command: string) {
  if (command.length > 2000) { state = { ...state, errors: ['Polecenie może mieć maksymalnie 2000 znaków.'] }; emit(); return false }
  const result = parseCommand(command, state.spec)
  if (result.errors.length) { state = { ...state, errors: result.errors }; emit(); return false }
  return updateStudio(result.spec, `Wykonano: ${result.applied.join(' · ')}. Obsługuję tylko parametry wymienione w panelu; inne szczegóły opisu wymagają podłączonego AI.`)
}
export function undoStudio() {
  const prior = state.history.at(-1)
  if (!prior) return
  state = { ...state, ...prior, revision: state.revision + 1, history: state.history.slice(0, -1), errors: [] }; emit()
}
