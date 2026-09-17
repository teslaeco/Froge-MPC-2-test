import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

describe('review-source English localization', () => {
  it('uses English dictation locale and user-facing microphone errors', () => {
    const source = readFileSync('src/studio/useDictation.ts', 'utf8')
    expect(source).toContain("r.lang = 'en-US'")
    expect(source).toContain('This browser does not support dictation.')
    expect(source).toContain('Microphone permission was not granted.')
    expect(source).toContain('The microphone could not be started.')
    expect(source).not.toMatch(/Ta przeglądarka|Brak zgody|Dyktowanie zatrzymane|Nie udało się uruchomić mikrofonu/)
  })

  it('keeps the research error fallback actionable in English', () => {
    const source = readFileSync('src/components/ResearchErrorBoundary.tsx', 'utf8')
    expect(source).toContain('This part of the report could not be displayed')
    expect(source).toContain('Try again')
    expect(source).toContain('Open research archive')
    expect(source).not.toMatch(/Nie udało się wyświetlić|Spróbuj ponownie|Otwórz archiwum badań/)
  })
})
