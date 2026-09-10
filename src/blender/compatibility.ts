// The worker builds its own scene plan. A visual-quality upgrade must not
// disable the preceding compatible prompt/job protocol.
// v7 fixed the profile regression and already uses the validated scene plan.
// v8–v11 change figure geometry; the prompt/job protocol remains compatible.
export const MINIMUM_CONNECTOR_VERSION = 7
export const RECOMMENDED_CONNECTOR_VERSION = 20
export const supportsCoutureQuality = (connection?: { connectorVersion?: number; coutureRevision?: number } | null) => (connection?.connectorVersion ?? 0) >= 19 && (connection?.coutureRevision ?? 0) >= 1
export const requiresCoutureQuality = (prompt: string) => /\b(couture|gown|sukni\w*|sukien\w*|wachlarz\w*)\b/i.test(prompt.normalize('NFKD'))
export const COUTURE_UPDATE_REASON = 'Ten strój wymaga generatora v19 na Oracle. Pobierz pełną paczkę i sprawdź serwer po instalacji. Zlecenie nie zostało wysłane do AI.'
export const supportsGeneration = (version?: number) => Number.isInteger(version) && (version ?? 0) >= MINIMUM_CONNECTOR_VERSION
export const supportsPhotoGeneration = (connection?: { connectorVersion?: number; photoInput?: boolean; provider?: string } | null) => (connection?.connectorVersion ?? 0) >= 14 && connection?.photoInput === true && connection.provider === 'openai'
export const supportsPortraitQuality = (connection?: { connectorVersion?: number; portraitRevision?: number } | null) => (connection?.connectorVersion ?? 0) >= 15 && (connection?.portraitRevision ?? 0) >= 1
export function requiresPortraitQuality(prompt: string, photoCount = 0) {
  if (photoCount > 0) return true
  const text=prompt.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replaceAll('ł','l').split(/\b(?:dla|for)\b/)[0]
  return /\b(kobiet\w*|dziewczyn\w*|mezczyzn\w*|chlopak\w*|czlowiek\w*|wokalist\w*|raper\w*|modelk\w*|portret\w*|woman|girl|man|human|person|portrait|cardi)\b/.test(text)
}
export const PORTRAIT_UPDATE_REASON = 'Ten model wymaga standardu postaci v15. Pobierz instalator poniżej i uruchom go w Oracle Cloud Shell, potem sprawdź połączenie. Zlecenie nie zostało wysłane do AI.'
